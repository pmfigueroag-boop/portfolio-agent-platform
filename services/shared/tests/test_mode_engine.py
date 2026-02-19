import pytest
import os
from services.shared.mode_engine import ModeMachine, SystemMode

def test_initial_mode_default():
    if "SYSTEM_MODE" in os.environ:
        del os.environ["SYSTEM_MODE"]
    mm = ModeMachine()
    assert mm.get_mode() == SystemMode.NORMAL
    assert mm.is_safe_to_execute() is True

def test_set_mode():
    mm = ModeMachine()
    mm.set_mode(SystemMode.PANIC)
    assert mm.get_mode() == SystemMode.PANIC
    assert mm.is_safe_to_execute() is False

def test_env_override():
    os.environ["SYSTEM_MODE"] = "FAIL_SAFE"
    mm = ModeMachine()
    assert mm.get_mode() == SystemMode.FAIL_SAFE
    assert mm.is_safe_to_execute() is True
    del os.environ["SYSTEM_MODE"]
