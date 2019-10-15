from typing import Iterator

__all__ = ["extract"]

_ld, _rd = "[", "]"


def extract(text: str) -> Iterator[str]:
    """
    Generator that extracts sigils from text.
    Works properly with nested sigils.

    :param text: The text to extract the sigils from.
    :return: An iterable of sigil strings.

    >>> # Extract simple sigils from text
    >>> list(extract("Connect to [ENV.HOST] as [USER]"))
    ['[ENV.HOST]', '[USER]']

    >>> # Nested sigils are allowed, only top level is extracted
    >>> list(extract("Environ [ENV=[SRC]]"))
    ['[ENV=[SRC]]']

    >>> # Malformed sigils are not extracted (no errors raised).
    >>> list(extract("Connect to [ENV.HOST as USER"))
    []
    """
    global _ld, _rd

    buffer, depth = [], 0
    for char in text:
        if char == _ld:
            depth += 1
        if depth > 0:
            buffer.append(char)
            if char == _rd:
                depth -= 1
                if depth == 0:
                    yield ''.join(buffer)
                    buffer.clear()
