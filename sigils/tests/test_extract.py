from ..extract import *


def test_extract_deep_nested():
    sigil = "[ENV=[USR=[CURRENT].DEFAULT_ENV].APP=[APP=[ACTIVE]]]"
    text = f"This text has a sigil {sigil} embedded on it"
    results = list(extract(text))
    assert results == [sigil]
