from enum import Enum
import os

class SystemMode(Enum):
    NORMAL = "NORMAL"
    FAIL_SAFE = "FAIL_SAFE"
    PANIC = "PANIC"

class ModeMachine:
    def __init__(self):
        self.current_mode = SystemMode(os.getenv("SYSTEM_MODE", "NORMAL"))
    
    def get_mode(self) -> SystemMode:
        return self.current_mode
    
    def set_mode(self, mode: SystemMode):
        self.current_mode = mode
        
    def is_safe_to_execute(self) -> bool:
        return self.current_mode in [SystemMode.NORMAL, SystemMode.FAIL_SAFE]
