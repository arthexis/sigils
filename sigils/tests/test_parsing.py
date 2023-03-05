import os
import pytest

from ..parsing import *  # Module under test

# TODO: Fix nested sigils
def test_extract_single_deep_nested():
    # Very exagerated example
    sigil = "[APP=[ENV=[REQUEST].USER]].OR=[ENV=[DEFAULT].USER].MODULE.NAME]]]"
    text = f"-- {sigil} --"
    assert set(pull(text)) == {sigil}


def test_ignore_whitespace():
    sigil = "[[ ENV . HELP ]]"
    text = f"-- {sigil} --"
    assert set(pull(text)) == {sigil}


def test_extract_file_stream():
    # Chdir to test data directory
    os.chdir(os.path.dirname(__file__))
    with open("data/sample.txt", "r") as fp:
        assert set(pull(fp)) == {"[[ENV.HOST]]"}


# Test both kinds of quotes used in sub sigils
def test_extract_sub_sigils():
    sigils = ["[[ENV.HOST]]", "[[ENV.HELLO='World']]", "[[ENV.HELLO=\"World\"]]"]
    text = f"-- {sigils[0]} -- {sigils[1]} -- {sigils[2]} --"
    assert set(pull(text)) == set(sigils)
    

# Test that parsing fails when a sub sigil is not closed
def test_parse_sub_sigil_not_closed():
    # TODO: This should not be extracted
    sigil = "[[ENV.HELLO='World]]"
    text = f"-- {sigil} --"
    assert set(pull(text)) == set()