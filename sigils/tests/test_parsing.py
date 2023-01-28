import os

from ..parsing import *  # Module under test


def test_extract_single_deep_nested():
    sigil = "[ENV=[USR=[CURRENT].DEFAULT_ENV].APP=[APP=[ACTIVE]]]"
    text = f"-- {sigil} --"
    assert set(extract(text)) == {sigil}


def test_ignore_whitespace():
    sigil = "[ ENV . HELP ]"
    text = f"-- {sigil} --"
    assert set(extract(text)) == {sigil}


def test_extract_file_stream():
    # Chdir to test data directory
    os.chdir(os.path.dirname(__file__))
    with open("data/sample.txt", "r") as fp:
        assert set(extract(fp)) == {"[ENV.HOST]"}
