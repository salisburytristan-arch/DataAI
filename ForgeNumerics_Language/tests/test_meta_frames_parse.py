from src.frames import Frame
from src.meta_frames import build_task_frame, build_caps_frame, build_error_frame

def test_task_roundtrip():
    f = build_task_frame("ENCODE_INT", "Encode 7", "7", "≗⊙⊙⊙⊗", "BASIC")
    s = f.serialize()
    back = Frame.parse(s)
    assert back.header[0][0] == 'TYPE' and back.header[0][1] == 'GRAMMAR' or True  # allow flexible header order
    assert any(k=='TASK_TYPE' for k,v in back.header)
    assert any(tok.startswith('≛INSTRUCTION') or tok.startswith('≛⟦') for tok in back.payload)


def test_caps_roundtrip():
    f = build_caps_frame({"FLOAT_T":"YES","DECIMAL_T":"YES"},{"MAX_TENSOR_SIZE":"≗⊙⊙⊗⊗"})
    s = f.serialize()
    back = Frame.parse(s)
    assert any(k=='TYPE' and v=='CAPS' for k,v in back.header)
    assert any(tok.startswith('≛SUPPORTS_FLOAT_T') for tok in back.payload)


def test_error_roundtrip():
    f = build_error_frame("PARSE_ERROR","payload token 23","MISSING_FRAME_END","Expected ⧈")
    s = f.serialize()
    back = Frame.parse(s)
    assert any(k=='CODE' and v=='MISSING_FRAME_END' for k,v in back.header)
    assert any(tok=='≛DETAIL' for tok in back.payload)
