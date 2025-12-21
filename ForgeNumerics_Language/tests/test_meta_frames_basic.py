from src import meta_frames as mf


def test_build_grammar_frame_serializes():
    f = mf.build_grammar_frame("rule := TOKEN;", version="x")
    s = f.serialize()
    assert "GRAMMAR" in s


def test_build_task_frame_serializes():
    f = mf.build_task_frame("TEST", "do it", "input", expected_output="out", difficulty="BASIC")
    s = f.serialize()
    assert "TASK" in s


def test_build_caps_frame_serializes():
    f = mf.build_caps_frame({"FEATURE": "YES"}, limits={"MAX": "≗⊙"})
    s = f.serialize()
    assert "CAPS" in s