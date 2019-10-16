from typing import Tuple, List

from .extract import extract

__all__ = ["replace"]


def replace(text: str, pattern: str) -> Tuple[str, List[str]]:
    """
    Replace all sigils in the text with another pattern.
    Returns the replaced text and a list of sigils in found order.
    This will not resolve the sigils by default.

    :param text: The text with the sigils to be replaced.
    :param pattern: A string used to replace the sigils with.
    :return: A tuple of: replaced text, list of sigil strings.

    >>> # Protect against SQL injection.
    >>> replace("select * from users where username = [USER]", "?")
    ('select * from users where username = ?', ['[USER]'])
    """

    sigils = list(extract(text))
    for sigil in set(sigils):
        text = text.replace(sigil, pattern)
    return text, sigils
