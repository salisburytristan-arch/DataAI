import os
from src.determinism import now
from src import conversation_cache as cc


def test_now_uses_fake_time():
    os.environ["ACX_FAKE_TIME"] = "123.456"
    assert now() == 123.456
    os.environ.pop("ACX_FAKE_TIME", None)


def test_cache_timestamp_respects_fake_time(tmp_path):
    os.environ["ACX_FAKE_TIME"] = "99.0"
    cc.set_block("proj", "block", "key", {"v": 1})
    entry = cc._CACHE[("proj", "block", "key")]
    assert entry["ts"] == 99.0
    os.environ.pop("ACX_FAKE_TIME", None)
    cc.invalidate()
