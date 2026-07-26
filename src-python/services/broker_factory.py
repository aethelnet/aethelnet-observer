from typing import Optional
from services.wallet import get_wallet, Wallet
from services.paper_broker import PaperBroker

class BrokerFactory:
    """
    Fabricates Broker instances connected to specific Sub-Wallets.
    """
    
    @staticmethod
    def get_broker(exchange_id: str, type: str = "paper") -> Any:
        # Get the global OmniWallet
        omni_wallet = get_wallet()
        
        # Get specific sub-wallet (auto-creates if missing)
        sub_wallet = omni_wallet.get_sub_wallet(exchange_id)
        
        if type == "paper":
            # Return a PaperBroker instance connected to this sub-wallet
            # NOTE: PaperBroker might have its own state (open orders).
            # We need to ensure we don't creating new Broker instances that lose that state
            # unless PaperBroker persists it keyed by something.
            # Currently PaperBroker assumes a Singleton pattern via 'get_broker'.
            # We should probably refactor PaperBroker to NOT be a singleton, 
            # OR have the Factory manage instances.
            
            return _get_persistent_broker(exchange_id, sub_wallet)
            
        elif type == "live":
            raise NotImplementedError("Live Broker not yet implemented in Phase 30.")
            
        else:
            raise ValueError(f"Unknown broker type: {type}")

# Internal Registry to ensure we return the SAME broker instance for the same ID
_broker_registry = {}

def _get_persistent_broker(exchange_id: str, wallet: Wallet):
    if exchange_id not in _broker_registry:
        # Create new
        # Note: PaperBroker's internal load_state might need differentiation
        # if multiple paper brokers exist?
        # Current PaperBroker.load_state uses "broker_state.json" hardcoded?
        # Let's check PaperBroker code.
        
        # We need to subclass or modify PaperBroker to support custom state filenames.
        # For now, let's treat 'binance_paper' as the legacy one using 'broker_state.json'
        # and others use unique names.
        
        state_file = "broker_state.json" 
        if exchange_id != "binance_paper":
            state_file = f"broker_state_{exchange_id}.json"
            
        broker = PaperBroker(wallet)
        # Monkey-patch save/load to use specific file? 
        # Or better, pass it? Broker doesn't accept file path in init.
        # It has explicit load_state(path).
        
        # Load state
        broker.load_state(state_file)
        
        # Monkey-patch the save method to use our file
        # (A bit dirty, but avoids refactoring PaperBroker deeply right now)
        original_save = broker.save_state
        def scoped_save(path=state_file):
            return original_save(path)
        broker.save_state = scoped_save
        
        _broker_registry[exchange_id] = broker
        
    return _broker_registry[exchange_id]
