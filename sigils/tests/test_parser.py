import os
import pytest

from ..parser import *  # Module under test
from ..tools import *  # Module under test

@pytest.mark.skip
def test_extract_slightly_nested():
    # Simple example
    sigil = "[[APP=[SYS.ENV.APP_NAME].MODULE.NAME]]"
    text = f"-- {sigil} --"
    assert set(spool(text)) == {sigil}

# TODO: Fix nested sigils
@pytest.mark.skip
def test_extract_single_deep_nested():
    # Very exagerated example
    sigil = "[[APP=[ENV=[REQUEST].USER]].OR=[ENV=[DEFAULT].USER].MODULE.NAME]]"
    text = f"-- {sigil} --"
    assert set(spool(text)) == {sigil}


def test_ignore_whitespace():
    sigil = "[[ ENV . HELP ]]"
    text = f"-- {sigil} --"
    assert set(spool(text)) == {sigil}


def test_extract_file_stream():
    # Chdir to test data directory
    os.chdir(os.path.dirname(__file__))
    with open("data/sample3.txt", "r") as fp:
        assert len(set(spool(fp))) == 3


# Test both kinds of quotes used in sub sigils
def test_extract_sub_sigils():
    sigils = ["[[ENV.HOST]]", "[[ENV.HELLO='World']]", "[[ENV.HELLO=\"World\"]]"]
    text = f"-- {sigils[0]} -- {sigils[1]} -- {sigils[2]} --"
    assert set(spool(text)) == set(sigils)
    

# Test that parsing fails when a sub sigil is not closed
def test_parse_sub_sigil_not_closed():
    # TODO: This should not be extracted
    sigil = "[[ENV.HELLO='World]]"
    text = f"-- {sigil} --"
    assert set(spool(text)) == set()
