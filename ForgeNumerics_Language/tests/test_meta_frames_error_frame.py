from src import meta_frames as mf


def test_build_error_frame_serializes():
    f = mf.build_error_frame("ERROR", "loc", "CODE", "detail", suggestion="fix")
    s = f.serialize()
    assert "ERROR" in s
    assert "CODE" in s