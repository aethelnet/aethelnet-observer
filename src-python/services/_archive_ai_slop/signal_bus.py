import asyncio
import logging
from collections import deque
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    """Represents a Signal emission event."""
    name: str
    source_id: str
    payload: Any
    timestamp: float

class SignalBus:
    """
    A lightweight Event Bus based on Godot's MessageQueue architecture.
    Decouples signal emission from execution to prevent recursion loops.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SignalBus, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        # Registry: Signal Name -> List of Subscribers (Callbacks)
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # Message Queue: Thread-safe deque (Append/PopLeft)
        # Stores (Signal) objects waiting for dispatch
        self._queue: deque = deque()
        
        self._is_running = False
        self.initialized = True
        logger.info("[SignalBus] Initialized (Godot Architecture).")

    def subscribe(self, signal_name: str, callback: Callable):
        """Connects a listener to a signal (Godot: connect())."""
        if signal_name not in self._subscribers:
            self._subscribers[signal_name] = []
        self._subscribers[signal_name].append(callback)
        logger.debug(f"[SignalBus] Subscribed to '{signal_name}'")

    def emit(self, signal_name: str, source_id: str, payload: Any = None):
        """
        Queues a signal for deferred execution (Godot: emit_signal()).
        Does NOT execute immediately to avoid locking the caller.
        """
        import time
        sig = Signal(
            name=signal_name,
            source_id=source_id,
            payload=payload,
            timestamp=time.time()
        )
        self._queue.append(sig)
        # logger.debug(f"[SignalBus] Queued signal '{signal_name}' from {source_id}")

    async def start_processing(self):
        """Main Event Loop (Godot: _process())."""
        self._is_running = True
        logger.info("[SignalBus] Processing Loop STARTED.")
        
        while self._is_running:
            await self._process_queue()
            # Yield control to allow other tasks to run (Non-blocking)
            await asyncio.sleep(0.01)

    async def _process_queue(self):
        """Flushes the current queue."""
        # Process up to N messages per frame to avoid starvation
        # Godot usually flushes all, but we limit to be safe in Python
        limit = 100 
        
        while self._queue and limit > 0:
            signal: Signal = self._queue.popleft()
            await self._dispatch(signal)
            limit -= 1

    async def _dispatch(self, signal: Signal):
        """Executes the callbacks for a signal."""
        if signal.name in self._subscribers:
            for callback in self._subscribers[signal.name]:
                try:
                    # Support both async and sync callbacks
                    if asyncio.iscoroutinefunction(callback):
                        await callback(signal.payload)
                    else:
                        callback(signal.payload)
                except Exception as e:
                    logger.error(f"[SignalBus] Error dispatching '{signal.name}': {e}")

    def stop(self):
        self._is_running = False
        logger.info("[SignalBus] Processing Loop STOPPED.")

# Global Singleton Accessor
def get_signal_bus() -> SignalBus:
    return SignalBus()
