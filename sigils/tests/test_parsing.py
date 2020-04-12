from ..parsing import *  # Module under test


def test_extract_single_deep_nested():
    sigil = "[ENV=[USR=[CURRENT].DEFAULT_ENV].APP=[APP=[ACTIVE]]]"
    text = f"-- {sigil} --"
    assert set(extract(text)) == {sigil}


def test_ignore_whitespace():
    sigil = "[ ENV . HELP ]"
    text = f"-- {sigil} --"
    assert set(extract(text)) == {sigil}
