from ..replace import *  # Module under test


def test_replace_duplicated():
    text = "User: [USER], Manager: [USER], Company: [ORG]"
    text, sigils = replace(text, "%s")
    assert text == "User: %s, Manager: %s, Company: %s"
    assert sigils == ["[USER]", "[USER]", "[ORG]"]
