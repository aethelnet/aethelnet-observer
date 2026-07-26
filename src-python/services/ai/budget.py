"""
AI Token Budget System

Tracks and limits AI API token usage with budget controls.
Completely optional - system works without any AI keys.

Features:
- Daily/weekly/monthly token caps
- Cost estimation before running
- Warnings at 50%, 80%, 100% of budget
- Usage history and analytics

Usage:
    from services.ai.budget import get_budget_manager
    
    budget = get_budget_manager()
    
    # Check before running
    if budget.can_spend(estimated_tokens=500):
        budget.record_usage(tokens=480, model="gpt-4", cost_usd=0.02)
    
    # Get status
    status = budget.get_status()
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: datetime
    tokens: int
    model: str
    cost_usd: float
    operation: str  # summarize, search, analyze, etc.
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class BudgetConfig:
    """Budget configuration."""
    daily_token_limit: int = 100_000      # ~$1-3 depending on model
    weekly_token_limit: int = 500_000     # ~$5-15
    monthly_token_limit: int = 2_000_000  # ~$20-60
    warning_threshold_50: bool = True
    warning_threshold_80: bool = True
    hard_limit_at_100: bool = True        # Stop processing at 100%


class BudgetManager:
    """
    Manages AI token budget with persistent tracking.
    
    Philosophy:
    - App works fully WITHOUT any AI
    - AI is a paid enhancement you control
    - Know exactly what each operation costs
    """
    
    # Approximate costs per 1K tokens (input/output averaged)
    MODEL_COSTS = {
        # OpenAI
        'gpt-4': 0.03,
        'gpt-4-turbo': 0.01,
        'gpt-3.5-turbo': 0.002,
        # Anthropic
        'claude-3-opus': 0.015,
        'claude-3-sonnet': 0.003,
        'claude-3-haiku': 0.00025,
        # Google
        'gemini-pro': 0.001,
        'gemini-flash': 0.0005,
        # Local (free)
        'ollama': 0.0,
        'local': 0.0,
    }
    
    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or os.getenv('BUDGET_DATA_DIR', './data/ai_budget'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = self.data_dir / 'config.json'
        self.usage_path = self.data_dir / 'usage.json'
        
        self.config = self._load_config()
        self.usage_history: List[UsageRecord] = self._load_usage()
        self._last_warning_level: Optional[int] = None
    
    def _load_config(self) -> BudgetConfig:
        """Load or create config."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = json.load(f)
                return BudgetConfig(**data)
            except Exception:
                pass
        return BudgetConfig()
    
    def _save_config(self):
        """Save config to disk."""
        with open(self.config_path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
    
    def _load_usage(self) -> List[UsageRecord]:
        """Load usage history."""
        if self.usage_path.exists():
            try:
                with open(self.usage_path) as f:
                    data = json.load(f)
                return [
                    UsageRecord(
                        timestamp=datetime.fromisoformat(r['timestamp']),
                        tokens=r['tokens'],
                        model=r['model'],
                        cost_usd=r['cost_usd'],
                        operation=r['operation']
                    )
                    for r in data
                ]
            except Exception:
                pass
        return []
    
    def _save_usage(self):
        """Save usage to disk."""
        # Keep only last 30 days
        cutoff = datetime.now() - timedelta(days=30)
        self.usage_history = [u for u in self.usage_history if u.timestamp > cutoff]
        
        with open(self.usage_path, 'w') as f:
            json.dump([u.to_dict() for u in self.usage_history], f, indent=2)
    
    # ==========================================
    # BUDGET CHECKING
    # ==========================================
    
    def can_spend(self, estimated_tokens: int) -> Dict[str, Any]:
        """
        Check if we can spend tokens within budget.
        
        Returns:
            {
                'allowed': bool,
                'reason': str,
                'daily_remaining': int,
                'weekly_remaining': int,
                'monthly_remaining': int,
                'warning_level': int (0, 50, 80, 100)
            }
        """
        daily = self.get_usage_for_period('daily')
        weekly = self.get_usage_for_period('weekly')
        monthly = self.get_usage_for_period('monthly')
        
        daily_remaining = self.config.daily_token_limit - daily
        weekly_remaining = self.config.weekly_token_limit - weekly
        monthly_remaining = self.config.monthly_token_limit - monthly
        
        min_remaining = min(daily_remaining, weekly_remaining, monthly_remaining)
        
        # Calculate warning level
        usage_pct = (monthly / self.config.monthly_token_limit) * 100 if self.config.monthly_token_limit > 0 else 0
        if usage_pct >= 100:
            warning_level = 100
        elif usage_pct >= 80:
            warning_level = 80
        elif usage_pct >= 50:
            warning_level = 50
        else:
            warning_level = 0
        
        # Check if allowed
        allowed = True
        reason = "OK"
        
        if self.config.hard_limit_at_100 and min_remaining < estimated_tokens:
            allowed = False
            if daily_remaining < estimated_tokens:
                reason = "Daily budget exceeded"
            elif weekly_remaining < estimated_tokens:
                reason = "Weekly budget exceeded"
            else:
                reason = "Monthly budget exceeded"
        
        return {
            'allowed': allowed,
            'reason': reason,
            'estimated_tokens': estimated_tokens,
            'daily_remaining': max(0, daily_remaining),
            'weekly_remaining': max(0, weekly_remaining),
            'monthly_remaining': max(0, monthly_remaining),
            'warning_level': warning_level
        }
    
    def get_usage_for_period(self, period: str) -> int:
        """Get token usage for a period (daily, weekly, monthly)."""
        now = datetime.now()
        
        if period == 'daily':
            cutoff = now - timedelta(days=1)
        elif period == 'weekly':
            cutoff = now - timedelta(weeks=1)
        elif period == 'monthly':
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(days=30)
        
        return sum(u.tokens for u in self.usage_history if u.timestamp > cutoff)
    
    # ==========================================
    # RECORDING USAGE
    # ==========================================
    
    def record_usage(
        self, 
        tokens: int, 
        model: str = 'gpt-4', 
        cost_usd: float = None,
        operation: str = 'unknown'
    ):
        """Record token usage."""
        # Calculate cost if not provided
        if cost_usd is None:
            cost_per_1k = self.MODEL_COSTS.get(model, 0.01)
            cost_usd = (tokens / 1000) * cost_per_1k
        
        record = UsageRecord(
            timestamp=datetime.now(),
            tokens=tokens,
            model=model,
            cost_usd=cost_usd,
            operation=operation
        )
        
        self.usage_history.append(record)
        self._save_usage()
        
        # Check for warnings
        self._check_warnings()
    
    def _check_warnings(self):
        """Check and emit budget warnings."""
        status = self.get_status()
        warning_level = status['warning_level']
        
        if warning_level > 0 and warning_level != self._last_warning_level:
            self._last_warning_level = warning_level
            # In a real implementation, this could emit events or notifications
            print(f"⚠️ AI Budget Warning: {warning_level}% of monthly budget used")
    
    # ==========================================
    # STATUS AND ANALYTICS
    # ==========================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get current budget status."""
        daily = self.get_usage_for_period('daily')
        weekly = self.get_usage_for_period('weekly')
        monthly = self.get_usage_for_period('monthly')
        
        # Calculate costs
        daily_cost = sum(u.cost_usd for u in self.usage_history 
                        if u.timestamp > datetime.now() - timedelta(days=1))
        monthly_cost = sum(u.cost_usd for u in self.usage_history 
                         if u.timestamp > datetime.now() - timedelta(days=30))
        
        # Warning level
        usage_pct = (monthly / self.config.monthly_token_limit) * 100 if self.config.monthly_token_limit > 0 else 0
        warning_level = 100 if usage_pct >= 100 else (80 if usage_pct >= 80 else (50 if usage_pct >= 50 else 0))
        
        return {
            'daily': {
                'used': daily,
                'limit': self.config.daily_token_limit,
                'remaining': max(0, self.config.daily_token_limit - daily),
                'percent': round((daily / self.config.daily_token_limit) * 100, 1) if self.config.daily_token_limit > 0 else 0
            },
            'weekly': {
                'used': weekly,
                'limit': self.config.weekly_token_limit,
                'remaining': max(0, self.config.weekly_token_limit - weekly),
                'percent': round((weekly / self.config.weekly_token_limit) * 100, 1) if self.config.weekly_token_limit > 0 else 0
            },
            'monthly': {
                'used': monthly,
                'limit': self.config.monthly_token_limit,
                'remaining': max(0, self.config.monthly_token_limit - monthly),
                'percent': round(usage_pct, 1)
            },
            'costs': {
                'today_usd': round(daily_cost, 4),
                'month_usd': round(monthly_cost, 4)
            },
            'warning_level': warning_level,
            'records_count': len(self.usage_history)
        }
    
    def estimate_cost(self, tokens: int, model: str = 'gpt-4') -> Dict[str, float]:
        """Estimate cost for a given token count."""
        cost_per_1k = self.MODEL_COSTS.get(model, 0.01)
        cost_usd = (tokens / 1000) * cost_per_1k
        
        return {
            'tokens': tokens,
            'model': model,
            'cost_per_1k_tokens': cost_per_1k,
            'estimated_cost_usd': round(cost_usd, 6)
        }
    
    def update_config(self, **kwargs):
        """Update budget configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self._save_config()


# Singleton
_budget_manager: Optional[BudgetManager] = None

def get_budget_manager() -> BudgetManager:
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager
