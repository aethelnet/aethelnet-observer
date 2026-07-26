import math
from typing import Any
from ouroboros.base import OuroborosNode, OuroborosParameter
from utils.airwindows_console import AirwindowsConsole

class AirwindowsNode(OuroborosNode):
    """
    An abstract Audio DSP filter that applies Golden Ratio Saturation and ClipOnly3 Mastering.
    Can be used by the LGNN to add "punch" or non-linear scaling to ANY data stream.
    """
    def __init__(self, node_id: str):
        # Instantiate the raw mathematical cores
        self.console_9 = AirwindowsConsole(flavor="console9")
        super().__init__(node_id)
        
    def _setup_parameters(self):
        # The LGNN can sweep these parameters to find the optimal saturation profile for the data
        self.parameters['headroom'] = OuroborosParameter("headroom", min_val=1.0, max_val=50.0, default=10.0)
        self.parameters['saturation_drive'] = OuroborosParameter("saturation_drive", min_val=0.1, max_val=2.0, default=1.0)
        
    def process(self, data_stream: Any) -> Any:
        """
        Expects a float. Scales it, saturates it, and expands it back.
        """
        # In a real Swarm, data_stream could be a tensor or a numpy array.
        # For now, we support single float processing (e.g. Z-Scores or Sensor readings).
        if not isinstance(data_stream, (float, int)):
            return data_stream # Pass through unhandled types for now
            
        headroom = self.get_parameter('headroom')
        drive = self.get_parameter('saturation_drive')
        
        # 1. Map into audio-space
        audio_val = (data_stream * drive) / headroom
        
        # 2. Golden Ratio Saturation
        encoded = self.console_9.encode(audio_val)
        decoded = self.console_9.decode(encoded)
        
        # 3. Mastering (ClipOnly3 slew-based limiter)
        mastered = self.console_9.master_desk(decoded)
        
        # 4. Expand back to domain space
        return mastered * headroom
