from app.services import msg_parser
import os

def test_parse_nonexistent_file():
    try:
        msg_parser.parse_msg_file("nonexistent.msg")
    except FileNotFoundError:
        assert True
    else:
        assert False
