import pytest
from src.frames import Frame, ParseError, HEADER_PAYLOAD_SEP, FRAME_START, FRAME_END


def test_parse_missing_separator_raises():
    bad = f"{FRAME_START}≛TYPE⦙≛ANSWER{FRAME_END}"  # no header/payload separator
    with pytest.raises(ParseError):
        Frame.parse(bad)


def test_parse_missing_end_raises():
    bad = f"{FRAME_START}≛TYPE⦙≛ANSWER{HEADER_PAYLOAD_SEP}≛PAYLOAD"
    with pytest.raises(ParseError):
        Frame.parse(bad)


def test_parse_malformed_header_field_raises():
    bad = f"{FRAME_START}≛TYPE⦙≛A⦙EXTRA{HEADER_PAYLOAD_SEP}≛P{FRAME_END}"
    with pytest.raises(ParseError):
        Frame.parse(bad)