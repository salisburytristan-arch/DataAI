import os
import random
import time
from contextlib import contextmanager

# Environment flags
ACX_TEST_MODE = os.environ.get("ACX_TEST_MODE") == "1"
ACX_SEED = os.environ.get("ACX_SEED")
ACX_FAKE_TIME = os.environ.get("ACX_FAKE_TIME")


def apply_seed():
    if ACX_SEED is None:
        return
    try:
        seed_val = int(ACX_SEED)
        random.seed(seed_val)
    except Exception:
        return


def now() -> float:
    # Re-read ACX_FAKE_TIME from environment each time for test flexibility
    fake_time = os.environ.get("ACX_FAKE_TIME")
    if fake_time is not None:
        try:
            return float(fake_time)
        except Exception:
            return time.time()
    return time.time()


@contextmanager
def deterministic_mode():
    prev_state = random.getstate()
    apply_seed()
    try:
        yield
    finally:
        random.setstate(prev_state)
