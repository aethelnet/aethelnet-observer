import asyncio
import logging
import time
from typing import Dict, List, Optional
from config.settings import get_settings
from services.brain import get_engine

logger = logging.getLogger("BeaconService")

class BaseDeAIPlug:
    """Base class for DeAI platform connectors."""
    def __init__(self, name: str):
        self.name = name
        self.settings = get_settings()

    async def submit_prediction(self, symbol: str, signal: float, confidence: float, metadata: Dict):
        """Submit a prediction to the platform. To be implemented by subclasses."""
        raise NotImplementedError

class OceanPlug(BaseDeAIPlug):
    """
    Ocean Protocol Predictoor Plug.
    Submits binary (Up/Down) predictions to the Ocean Predictoor feeds.
    """
    def __init__(self):
        super().__init__("OceanPredictoor")
        self._lock = asyncio.Lock()  # Prevent nonce collisions on Oasis Sapphire
    
    async def submit_prediction(self, symbol: str, signal: float, confidence: float, metadata: Dict):
        # Ocean Predictoor typically wants a binary prediction: 
        # 0 (Low/Down) or 1 (High/Up)
        # We derive this from our internal signal (usually Z-Score)
        prediction_val = 1 if signal > 0 else 0
        
        # Formatting for Ocean Smart Contract / API
        # True = Price will be higher in T+5m
        # False = Price will be lower in T+5m
        is_up = bool(prediction_val)
        
        # LOGGING for verification
        logger.info(f"[OCEAN] Prepared prediction for {symbol}: {'UP' if is_up else 'DOWN'} (Signal: {signal:.2f}, Confidence: {confidence:.2f})")
        
        # 4. REAL SUBMISSION LOGIC (Wet Run Connectivity Check)
        async with self._lock:
            try:
                # Check keys first
                pk = self.settings.OCEAN_PRIVATE_KEY
                if not pk or "placeholder" in str(pk).lower():
                    if self.settings.DEAI_LOG_ONLY:
                         return True # Silent continue in dry run if no keys
                    logger.warning("[OCEAN] Private Key is placeholder. Skipping Wet Run.")
                    return False

                pk_str = pk.get_secret_value() if hasattr(pk, 'get_secret_value') else str(pk)
                
                # --- CONNECTIVITY CHECK (Safe Read-Only) ---
                from web3 import Web3
                from eth_account import Account
                
                # Sapphire RPC Configuration
                # Prioritize settings-defined URL (e.g. for Testnet or Private Node)
                rpc_urls = ["https://sap.oasis.io", "https://sapphire.oasis.io", "https://1rpc.io/oasis/sapphire"]
                
                custom_rpc = getattr(self.settings, "OCEAN_NETWORK_URL", None)
                if custom_rpc and "http" in custom_rpc:
                    # Prepend custom RPC to the list
                    rpc_urls.insert(0, custom_rpc)
                
                web3 = None
                last_err = None
                
                for rpc in rpc_urls:
                    try:
                        w3_candidate = Web3(Web3.HTTPProvider(rpc))
                        if w3_candidate.is_connected():
                             web3 = w3_candidate
                             break
                    except Exception as e:
                        last_err = e
                        continue
                
                if not web3:
                    logger.error(f"[OCEAN] Could not connect to Sapphire RPCs. Last error: {last_err}")
                    return False

                account = Account.from_key(pk_str)
                
                # Gas Check acts as "Auth Verify"
                balance = web3.eth.get_balance(account.address)
                balance_eth = web3.from_wei(balance, 'ether')
                
                # LOG SUCCESS
                logger.info(f"[OCEAN] Wet Run Ready: Wallet {account.address[:6]}... Balance: {balance_eth} ROSE")
                
                # --- SAFETY GATE ---
                if self.settings.DEAI_LOG_ONLY:
                    logger.info(f"[OCEAN][DRY-RUN] Connectivity Verified. Skipping transaction.")
                    return True

                gas_price = web3.eth.gas_price
                if balance < gas_price * 21000:
                    logger.error("[OCEAN] Insufficient Gas for prediction.")
                    return False
                    
                # Contracts (Sapphire Mainnet - 5m)
                # Source: Ocean Protocol Github / Predictoor Data
                CONTRACT_MAP = {
                    "BTCUSDC": "0x247738f65B7D7c35F973273180295A213c49e21f", # BTC/USDT 5m
                    "ETHUSDC": "0x272449a8B4E17D31C72E06eB83D1B463C4aE40e3", # ETH/USDT 5m
                    "BNBUSDC": "0x...", # Add more if found
                }
                
                contract_addr = CONTRACT_MAP.get(symbol)
                if not contract_addr or "..." in contract_addr:
                    # Fallback
                    if symbol not in ["BTCUSDC", "ETHUSDC"]:
                         logger.info(f"[OCEAN] Symbol {symbol} not mapped to a live contract. Skipping stake.")
                         return True
                
                # Ensure Checksum
                contract_addr = web3.to_checksum_address(contract_addr)
                
                # Epoch Calculation (5-min bucket)
                # Prediction is for the *next* epoch closure?
                # Predictoor logic: submit for epoch T. 
                import time
                ts = int(time.time())
                epoch = (ts // 300) * 300
                # Usually we predict for 1 epoch ahead or current open epoch.
                # Standard ocean template: epoch = start of current block interval
                
                # ABI Minimal
                # function submitPrediction(uint256 epoch, bool isUp, uint256 stake)
                abi = [{
                    "inputs": [
                        {"internalType": "uint256", "name": "epoch", "type": "uint256"},
                        {"internalType": "bool", "name": "isUp", "type": "bool"},
                        {"internalType": "uint256", "name": "stake", "type": "uint256"}
                    ],
                    "name": "submitPrediction",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }]
                
                contract = web3.eth.contract(address=contract_addr, abi=abi)
                
                # Stake Amount (in WEI)
                stake_rose = self.settings.ORACLE_STAKE_LIMIT # e.g. 0.01
                stake_wei = web3.to_wei(stake_rose, 'ether')
                
                # Build Transaction
                nonce = web3.eth.get_transaction_count(account.address)
                tx = contract.functions.submitPrediction(
                    epoch, 
                    is_up, 
                    stake_wei
                ).build_transaction({
                    'chainId': 23294, # Sapphire Mainnet
                    'gas': 300000,    # Encrypted execution needs closer to 200k+
                    'gasPrice': web3.eth.gas_price,
                    'nonce': nonce,
                })
                
                # Sign & Send
                signed_tx = web3.eth.account.sign_transaction(tx, private_key=pk_str)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                logger.info(f"[OCEAN] 🌊 LIVE STAKE SUBMITTED! {symbol} {'UP' if is_up else 'DOWN'} | Stake: {stake_rose} ROSE | Tx: {web3.to_hex(tx_hash)}")
                return True
                
            except Exception as e:
                logger.error(f"[OCEAN] Submission Error: {e}")
                return False

class NumeraiPlug(BaseDeAIPlug):
    """
    Numerai Signals Plug.
    Submits stock market signals to the Numerai Signals platform.
    """
    def __init__(self):
        super().__init__("NumeraiSignals")
        self.model_id = self.settings.NUMERAI_MODEL_NAME
        self.buffer = []  # Initialize buffer for batch uploads
    
    async def submit_prediction(self, symbol: str, signal: float, confidence: float, metadata: Dict):
        import math
        prediction_val = 0.5 + (0.5 * math.tanh(signal))
        
        # Buffer the signal
        self.buffer.append({
            "ticker": symbol,
            "signal": prediction_val,
            "model_id": self.model_id
        })
        logger.info(f"[NUMERAI] Buffered signal for {symbol}: {prediction_val:.4f}")
        return True

    def flush(self):
        """Submit predictions for FULL Numerai live universe (~5000 stocks)."""
        try:
            import pandas as pd
            import numerapi
            import os
            import random
            
            pub_id = self.settings.NUMERAI_PUBLIC_ID
            sec_key = self.settings.NUMERAI_SECRET_KEY
            model_name = self.settings.NUMERAI_MODEL_NAME
            
            if not pub_id or not sec_key:
                if not self.settings.DEAI_LOG_ONLY:
                    logger.warning("[NUMERAI] Keys missing. Skipping Flush.")
                self.buffer = []
                return

            p_id = pub_id.get_secret_value() if hasattr(pub_id, 'get_secret_value') else str(pub_id)
            s_key = sec_key.get_secret_value() if hasattr(sec_key, 'get_secret_value') else str(sec_key)
            
            if "placeholder" in p_id.lower() or self.settings.DEAI_LOG_ONLY:
                 logger.info(f"[NUMERAI][DRY-RUN] Would submit signals for model {model_name}")
                 self.buffer = []
                 return
                 
            napi = numerapi.SignalsAPI(public_id=p_id, secret_key=s_key)
            
            # 1. Fetch FULL Numerai ticker universe
            # Note: napi.ticker_universe() is unreliable/broken on v2.
            # We download the live parquet file directly.
            try:
                # Remove cached file if exists
                if os.path.exists("live_universe.parquet"):
                    os.remove("live_universe.parquet")
                    
                logger.info("[NUMERAI] Downloading live universe parquet...")
                napi.download_dataset("signals/v2.0/live.parquet", "live_universe.parquet")
                
                # Check if pyarrow/fastparquet is available (we installed pyarrow)
                u_df = pd.read_parquet("live_universe.parquet")
                
                # Extract tickers
                if 'numerai_ticker' in u_df.columns:
                    universe = u_df['numerai_ticker'].tolist()
                elif 'ticker' in u_df.columns:
                    universe = u_df['ticker'].tolist()
                else:
                    logger.error(f"[NUMERAI] Parquet missing ticker column. Cols: {u_df.columns.tolist()}")
                    self.buffer = []
                    return
                    
                logger.info(f"[NUMERAI] Fetched live universe: {len(universe)} tickers")
                
                # Cleanup parquet
                os.remove("live_universe.parquet")
                
            except Exception as e:
                logger.error(f"[NUMERAI] Failed to fetch universe: {e}")
                self.buffer = []
                return
            
            if not universe or len(universe) < 100:
                logger.error(f"[NUMERAI] Universe too small ({len(universe) if universe else 0}). Aborting.")
                self.buffer = []
                return
            
            # 2. Map our buffered signals to universe tickers
            buffered_signals = {}
            for item in self.buffer:
                ticker = item.get('ticker', '').upper()
                if ticker:
                    buffered_signals[ticker] = item['signal']
            
            # 3. Generate predictions for ALL universe tickers
            predictions = []
            signals_applied = 0
            
            for ticker in universe:
                ticker_upper = ticker.upper()
                
                if ticker_upper in buffered_signals:
                    # Use our actual signal
                    signal = buffered_signals[ticker_upper]
                    signals_applied += 1
                else:
                    # Neutral prediction with tiny variance (Numerai requires unique values)
                    signal = 0.5 + random.uniform(-0.02, 0.02)
                
                # Clamp to valid range (exclusive 0-1)
                signal = max(0.001, min(0.999, signal))
                predictions.append({'ticker': ticker, 'signal': round(signal, 6)})
            
            logger.info(f"[NUMERAI] Built predictions: {len(predictions)} total, {signals_applied} from our analysis")
            
            # 4. Lookup model UUID
            model_uuid = None
            if model_name:
                try:
                    models = napi.get_models()
                    for m in models:
                        if m.lower() == model_name.lower():
                            model_uuid = models[m]
                            break
                    if not model_uuid:
                        logger.warning(f"[NUMERAI] Model '{model_name}' not found in account. Check if model needs to be created.")
                except Exception as e:
                    logger.warning(f"[NUMERAI] Could not lookup model UUID: {e}")
            
            # 5. Submit as CSV file (API expects filepath)
            df = pd.DataFrame(predictions)
            filename = f"numerai_submission_{int(time.time())}.csv"
            df.to_csv(filename, index=False)
            
            logger.info(f"[NUMERAI] Uploading {len(df)} predictions to model {model_name} (UUID: {model_uuid})...")
            
            napi.upload_predictions(filename, model_id=model_uuid)
            logger.info("[NUMERAI] ✅ Full Universe Upload Successful!")
            
            # Cleanup
            self.buffer = []
            if os.path.exists(filename):
                os.remove(filename)
            
        except Exception as e:
            logger.error(f"[NUMERAI] Flush Failed: {e}")
            # Keep buffer? Or clear to prevent retry spam? 
            # Clear it to avoid getting stuck
            self.buffer = []

class BeaconService:
    """
    Passive Oracle Service: Broadcasts brain signals to DeAI platforms.
    Runs as a background task independently of trade execution.
    """
    def __init__(self):
        self.settings = get_settings()
        self.engine = get_engine()
        self.plugs: List[BaseDeAIPlug] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.plug_status: Dict[str, Dict] = {} # {name: {last_broadcast: float, success: bool, count: int}}

    def add_plug(self, plug: BaseDeAIPlug):
        """Register a new platform connector."""
        self.plugs.append(plug)
        self.plug_status[plug.name] = {
            "last_broadcast": 0,
            "success": True,
            "count": 0,
            "last_error": None
        }
        logger.info(f"[BEACON] Registered plug: {plug.name}")

    def get_status(self) -> Dict:
        """Return the current status of all DeAI plugs."""
        return {
            "running": self._running,
            "plugs": self.plug_status,
            "total_broadcasts": sum(p["count"] for p in self.plug_status.values())
        }

    async def start(self):
        """Start the background broadcast loop."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("[BEACON] Passive Oracle Service STARTED.")

    async def stop(self):
        """Stop the background loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[BEACON] Passive Oracle Service STOPPED.")

    async def _loop(self):
        """Main heartbeat loop."""
        # Force initial broadcast on startup
        logger.info("[BEACON] Initializing first broadcast cycle...")
        try:
            await self._broadcast()
        except Exception as e:
            logger.error(f"[BEACON] Initial broadcast failed: {e}")

        while self._running:
            try:
                await asyncio.sleep(300) # 5 Minute cycle
                await self._broadcast()
            except Exception as e:
                logger.error(f"[BEACON] Loop Error: {e}")
                await asyncio.sleep(60)

    async def _broadcast(self):
        """Internal broadcast logic to be shared between loop and manual trigger."""
        if not self.plugs:
            return

        # Get whitelist from settings
        from config.settings import get_trading_symbols
        symbols = get_trading_symbols(self.settings)

        for symbol in symbols:
            # DEBUG: Trace every symbol attempt
            # logger.info(f"[BEACON] Attempting {symbol}...") # Commented out to avoid spam, but I'll use a selective one
            if "BTC" in symbol or "ETH" in symbol:
                logger.debug(f"[BEACON] Trace {symbol}: Checking metrics...")
                
            # Only process symbols the brain has data for
            metrics = self.engine.get_latest_metrics(symbol)
            if not metrics:
                continue

            # Synchronize with Execution Logic: Prioritize Neural Signal
            # 1.0 = Strong Up, -1.0 = Strong Down
            signal = metrics.get('neural_signal', metrics.get('z_score', 0))
            confidence = metrics.get('confidence', metrics.get('stability', 0.5))
            
            # REPUTATION PROTECTION: Skip weak/neutral signals
            # Only broadcast meaningful predictions to protect Numerai reputation
            MIN_SIGNAL_STRENGTH = 0.3  # Minimum |Z-Score| to broadcast
            if abs(signal) < MIN_SIGNAL_STRENGTH:
                continue  # Skip this symbol - no meaningful signal
            
            # Get divine metrics for advanced plugs
            divine = self.engine.get_divine_metrics(symbol) or {}
            
            metadata = {
                "phase": divine.get("phase", 0),
                "dmd_forecast": divine.get("dmd_forecast", 0),
                "regime": divine.get("regime", 0),
                "price": metrics.get("price", 0)
            }

            # Broadcast to all registered plugs
            for plug in self.plugs:
                try:
                    # ALWAYS call submit_prediction to run connectivity checks internally
                    # The DEAI_LOG_ONLY gate is now effectively inside the plug logic
                    # to allow for "Auth Verification" logs without executing trades.
                        
                    await plug.submit_prediction(symbol, signal, confidence, metadata)
                    self.plug_status[plug.name]["last_broadcast"] = time.time()
                    self.plug_status[plug.name]["success"] = True
                    self.plug_status[plug.name]["count"] += 1
                    self.plug_status[plug.name]["last_error"] = None
                except Exception as e:
                    logger.error(f"[BEACON] Plug {plug.name} failed for {symbol}: {e}")
                    self.plug_status[plug.name]["success"] = False
                    self.plug_status[plug.name]["last_error"] = str(e)
        
        # End of cycle: Flush buffered predictions (Batch Upload)
        for plug in self.plugs:
            if hasattr(plug, 'flush'):
                 try:
                     plug.flush()
                 except Exception as e:
                     logger.error(f"[BEACON] Failed to flush plug {plug.name}: {e}")

# Singleton Instance
_beacon_instance: Optional[BeaconService] = None

def get_beacon() -> BeaconService:
    global _beacon_instance
    if _beacon_instance is None:
        _beacon_instance = BeaconService()
    return _beacon_instance
