"""
Order Tracker Service
Tracks orders placed from opportunities and manages their lifecycle.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger("OrderTracker")


class OpportunityOrderTracker:
    """
    Tracks orders placed from opportunities.
    
    Maintains mapping between opportunity IDs and their associated orders:
    - Entry orders (limit orders waiting to fill)
    - Take-profit orders (placed after entry fills)
    - Stop-loss orders (placed after entry fills)
    """
    
    def __init__(self):
        # opportunity_id -> {
        #   'entry_order_id': str,
        #   'entry_status': 'pending' | 'filled' | 'cancelled',
        #   'tp_order_id': Optional[str],
        #   'sl_order_id': Optional[str],
        #   'placed_at': datetime,
        #   'filled_at': Optional[datetime],
        #   'opportunity': Dict (snapshot of opportunity at placement time)
        # }
        self.opportunity_orders: Dict[str, Dict[str, Any]] = {}
        # order_id -> allocation info
        self.order_allocations: Dict[str, Dict[str, Any]] = {}
    
    def register_order(
        self,
        opportunity_id: str,
        order_id: str,
        order_type: str,
        opportunity_snapshot: Dict[str, Any]
    ) -> None:
        """
        Register an order linked to an opportunity.
        
        Args:
            opportunity_id: Unique opportunity ID
            order_id: Order ID from broker
            order_type: 'entry', 'take_profit', or 'stop_loss'
            opportunity_snapshot: Snapshot of opportunity data at placement time
        """
        if opportunity_id not in self.opportunity_orders:
            self.opportunity_orders[opportunity_id] = {
                'entry_order_id': None,
                'entry_status': 'pending',
                'tp_order_id': None,
                'sl_order_id': None,
                'placed_at': datetime.now(timezone.utc).isoformat(),
                'filled_at': None,
                'opportunity': opportunity_snapshot
            }
        
        if order_type == 'entry':
            self.opportunity_orders[opportunity_id]['entry_order_id'] = order_id
        elif order_type == 'take_profit':
            self.opportunity_orders[opportunity_id]['tp_order_id'] = order_id
        elif order_type == 'stop_loss':
            self.opportunity_orders[opportunity_id]['sl_order_id'] = order_id
    
    def update_order_status(
        self,
        order_id: str,
        status: str
    ) -> Optional[str]:
        """
        Update order status and return associated opportunity ID if found.
        
        Args:
            order_id: Order ID to update
            status: New status ('filled', 'cancelled', etc.)
        
        Returns:
            Opportunity ID if order is tracked, None otherwise
        """
        for opp_id, order_info in self.opportunity_orders.items():
            if order_info.get('entry_order_id') == order_id:
                if status == 'filled':
                    order_info['entry_status'] = 'filled'
                    order_info['filled_at'] = datetime.now(timezone.utc).isoformat()
                elif status == 'cancelled':
                    order_info['entry_status'] = 'cancelled'
                return opp_id
            elif order_info.get('tp_order_id') == order_id:
                if status == 'filled':
                    # Take-profit hit - opportunity completed
                    order_info['entry_status'] = 'completed'
                    order_info['completed_at'] = datetime.now(timezone.utc).isoformat()
                return opp_id
            elif order_info.get('sl_order_id') == order_id:
                if status == 'filled':
                    # Stop-loss hit - opportunity completed
                    order_info['entry_status'] = 'completed'
                    order_info['completed_at'] = datetime.now(timezone.utc).isoformat()
                return opp_id
        
        return None
    
    def get_opportunity_orders(self, opportunity_id: str) -> Optional[Dict[str, Any]]:
        """
        Get all order information for an opportunity.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            Order information dict or None if not found
        """
        return self.opportunity_orders.get(opportunity_id)
    
    def get_order_status(self, opportunity_id: str) -> str:
        """
        Get current order status for an opportunity.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            Status: 'pending', 'filled', 'completed', 'cancelled', or 'none'
        """
        order_info = self.opportunity_orders.get(opportunity_id)
        if not order_info:
            return 'none'
        return order_info.get('entry_status', 'none')
    
    def get_all_pending_orders(self) -> List[Dict[str, Any]]:
        """
        Get all opportunities with pending entry orders.
        
        Returns:
            List of opportunity order info dicts
        """
        pending = []
        for opp_id, order_info in self.opportunity_orders.items():
            if order_info.get('entry_status') == 'pending':
                pending.append({
                    'opportunity_id': opp_id,
                    **order_info
                })
        return pending
    
    def get_active_orders_with_allocation(self, pools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get all active orders (pending, filled) with allocation from specified pools.
        
        Args:
            pools: List of pool names to filter by. If None, returns all active orders with allocation.
        
        Returns:
            List of order info dicts with allocation info
        """
        active_statuses = ['pending', 'filled', 'active']
        active_orders = []
        
        for opp_id, order_info in self.opportunity_orders.items():
            status = order_info.get('entry_status', 'none')
            if status in active_statuses:
                entry_order_id = order_info.get('entry_order_id')
                if entry_order_id:
                    allocation_info = self.get_allocation_info(entry_order_id)
                    if allocation_info:
                        source = allocation_info.get('allocation_source')
                        # Filter by pools if specified
                        if pools is None or source in pools:
                            active_orders.append({
                                'opportunity_id': opp_id,
                                'order_id': entry_order_id,
                                'status': status,
                                'allocation': {
                                    'source': source,
                                    'amount': allocation_info.get('allocation_amount', 0)
                                },
                                **order_info
                            })
        
        return active_orders
    
    def store_allocation_info(self, order_id: str, opportunity_id: str, 
                             allocation_source: str, allocation_amount: float):
        """
        Store allocation info for an order.
        
        Args:
            order_id: Order ID
            opportunity_id: Opportunity ID
            allocation_source: Budget pool source (trading_pool, whitelist, etc.)
            allocation_amount: Amount allocated
        """
        import time
        self.order_allocations[order_id] = {
            'opportunity_id': opportunity_id,
            'allocation_source': allocation_source,
            'allocation_amount': allocation_amount,
            'timestamp': time.time()
        }
        logger.info(f"[OrderTracker] Stored allocation info for order {order_id}: ${allocation_amount:.2f} from {allocation_source}")
    
    def get_allocation_info(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get allocation info for an order.
        
        Args:
            order_id: Order ID
        
        Returns:
            Allocation info dict or None if not found
        """
        return self.order_allocations.get(order_id)
    
    def remove_allocation_info(self, order_id: str):
        """
        Remove allocation info for an order.
        
        Args:
            order_id: Order ID
        """
        self.order_allocations.pop(order_id, None)
    
    def cancel_opportunity_order(self, opportunity_id: str) -> bool:
        """
        Cancel an opportunity order (marks as cancelled) and return allocated funds.
        
        Args:
            opportunity_id: Opportunity ID
        
        Returns:
            True if cancelled, False if not found
        """
        if opportunity_id in self.opportunity_orders:
            order_info = self.opportunity_orders[opportunity_id]
            order_id = order_info.get('entry_order_id')
            
            # Return funds if allocation exists
            if order_id:
                allocation_info = self.get_allocation_info(order_id)
                if allocation_info:
                    allocation_amount = allocation_info.get('allocation_amount', 0)
                    allocation_source = allocation_info.get('allocation_source', 'unknown')
                    
                    # Remove allocation info to mark funds as returned
                    # The allocation tracking is for budget management - removing it
                    # effectively returns the funds to the pool for tracking purposes
                    self.remove_allocation_info(order_id)
                    
                    logger.info(
                        f"[OrderTracker] Order {order_id} cancelled. "
                        f"Returned ${allocation_amount:.2f} to {allocation_source} pool"
                    )
                    
                    # Note: Actual wallet balance doesn't need to be updated here because:
                    # 1. Limit orders don't lock funds until they fill
                    # 2. The allocation tracking is for budget/pool management only
                    # 3. If funds were locked (filled orders), they're handled by the broker
            
            order_info['entry_status'] = 'cancelled'
            order_info['cancelled_at'] = datetime.now(timezone.utc).isoformat()
            return True
        return False


# Singleton instance
_order_tracker_instance: Optional[OpportunityOrderTracker] = None


def get_order_tracker() -> OpportunityOrderTracker:
    """Get or create the singleton OpportunityOrderTracker instance."""
    global _order_tracker_instance
    if _order_tracker_instance is None:
        _order_tracker_instance = OpportunityOrderTracker()
    return _order_tracker_instance

