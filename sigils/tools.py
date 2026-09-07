"""Built-in transformation tools used by the Sigils resolver.

The public registry is explicit rather than discovered dynamically. This keeps
helper functions private, makes optional dependencies predictable, and avoids
the historical import-time patching layer.
"""

import base64 as _base64
import builtins as _builtins
import calendar
import hashlib
import json as _json
import math
import os
import random
import socket
import time as _time
import tomllib
import urllib.parse

DEFAULT_ENV_ALLOWLIST = frozenset(
    {
        "HOME",
        "LANG",
        "LC_ALL",
        "PATH",
        "PWD",
        "SHELL",
        "TERM",
        "TZ",
        "USER",
        "USERNAME",
    }
)


def lower(value):
    return str(value).lower()


def upper(value):
    return str(value).upper()


def trim(value):
    return str(value).strip()


def slugify(value):
    return str(value).lower().replace(" ", "-")


def reverse(value):
    text = str(value)
    if "," in text:
        return ",".join(text.split(",")[::-1])
    return text[::-1]


def capitalize(value):
    return str(value).capitalize()


def title(value):
    return str(value).title()


def count(value, substring):
    return str(value).count(str(substring))


def replace(value, old, new):
    return str(value).replace(str(old), str(new))


def first(value, n="1"):
    return str(value)[: int(n)]


def last(value, n="1"):
    return str(value)[-int(n) :]


def before(value, substring):
    return str(value).split(str(substring), 1)[0]


def after(value, substring):
    return str(value).split(str(substring), 1)[1]


def between(value, start, end):
    return str(value).split(str(start), 1)[1].split(str(end), 1)[0]


def strip(value, substring):
    return str(value).replace(str(substring), "")


def zfill(value, n):
    return str(value).zfill(int(n))


def _environment_allowlist():
    configured = os.environ.get("SIGILS_ENV_ALLOWLIST", "")
    additional = {
        item.strip().upper() for item in configured.split(",") if item.strip()
    }
    return DEFAULT_ENV_ALLOWLIST | additional


def env(value):
    allowlist = _environment_allowlist()
    if not value:
        return {
            key: item for key, item in os.environ.items() if key.upper() in allowlist
        }
    name = str(value).upper()
    if name not in allowlist:
        return ""
    return os.environ.get(name)


def epoch(value):
    if value:
        return _time.time() - int(value)
    return _time.time()


def sigil(value, start="[", end="]"):
    return f"{start}{value}{end}"


def nth(value, n, delimiter=","):
    return str(value).split(delimiter)[int(n)]


def split(value, delimiter=",", separator=","):
    return separator.join(str(value).split(delimiter))


def month(value):
    if not value:
        return calendar.month_name[_time.localtime().tm_mon]
    return calendar.month_name[int(value)]


def day(value):
    if not value:
        return calendar.day_name[_time.localtime().tm_wday]
    return calendar.day_name[int(value)]


def year(value):
    if not value:
        return _time.localtime().tm_year
    return _time.localtime(int(value)).tm_year


def date(value, fmt="%Y-%m-%d"):
    if not value:
        return _time.strftime(fmt)
    return _time.strftime(fmt, _time.localtime(int(value)))


def time(value, fmt="%H:%M:%S"):
    if not value:
        return _time.strftime(fmt)
    return _time.strftime(fmt, _time.localtime(int(value)))


def zodiac(value):
    timestamp = None if not value else int(value)
    current = _time.localtime(timestamp)
    month_number = current.tm_mon
    day_number = current.tm_mday
    boundaries = (
        ((12, 22), "Capricorn"),
        ((11, 22), "Sagittarius"),
        ((10, 23), "Scorpio"),
        ((9, 23), "Libra"),
        ((8, 23), "Virgo"),
        ((7, 23), "Leo"),
        ((6, 21), "Cancer"),
        ((5, 21), "Gemini"),
        ((4, 20), "Taurus"),
        ((3, 20), "Aries"),
        ((2, 18), "Pisces"),
        ((1, 20), "Aquarius"),
    )
    for boundary, name in boundaries:
        if (month_number, day_number) >= boundary:
            return name
    return "Capricorn"


def weekday(value):
    if not value:
        return calendar.day_name[_time.localtime().tm_wday]
    return calendar.day_name[_time.localtime(int(value)).tm_wday]


def rand(value):
    if not value:
        return random.random()
    return random.random() * float(value)


def randint(value):
    return str(random.randint(0, int(value)))


def choice(value):
    return random.choice(str(value).split(","))


def shuffle(value):
    items = str(value).split(",")
    random.shuffle(items)
    return ",".join(items)


def sample(value, n="1"):
    items = str(value).split(",")
    random.shuffle(items)
    return ",".join(items[: int(n)])


def join(value, delimiter=","):
    return delimiter.join(str(value).split(","))


def sort(value):
    items = str(value).split(",")
    items.sort()
    return ",".join(items)


def hide(value):
    return "*" * len(str(value))


def mask(value, n="4"):
    text = str(value)
    visible = int(n)
    return "*" * _builtins.max(0, len(text) - visible) + text[-visible:]


def truncate(value, n="50", ellipsis="..."):
    return str(value)[: int(n)] + ellipsis


def pad(value, n="50", character=" "):
    return str(value).ljust(int(n), character)


def scramble(value):
    items = list(str(value))
    random.shuffle(items)
    return "".join(items)


def tag(value, tag="div", attributes=""):
    separator = " " if attributes else ""
    return f"<{tag}{separator}{attributes}>{value}</{tag}>"


def link(value, url):
    return f'<a href="{url}">{value}</a>'


def image(value, url):
    return f'<img src="{url}" alt="{value}">'


def style(value, style):
    return f"<style>{style}</style>{value}"


def script(value, script):
    return f"<script>{script}</script>{value}"


def html(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _select(value, index):
    return value if index is None else value[index]


def json(value, index=None):
    return _select(_json.loads(value), index)


def toml(value, index=None):
    return _select(tomllib.loads(value), index)


def yaml(value, index=None):
    try:
        import yaml as _yaml
    except ImportError as exc:
        raise RuntimeError("YAML support requires pip install sigils[yaml]") from exc
    return _select(_yaml.safe_load(value), index)


def markdown(value):
    try:
        import markdown as _markdown
    except ImportError as exc:
        raise RuntimeError(
            "Markdown support requires pip install sigils[markdown]"
        ) from exc
    return _markdown.markdown(value)


def multiply(value, n):
    text = str(value)
    try:
        return str(float(text) * float(n))
    except ValueError:
        return text * int(n)


def roman(value):
    decimal = int(value)
    if decimal == 0:
        return "0"
    if decimal < 0:
        return "-" + roman(str(-decimal))
    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    result = []
    for number, numeral in numerals:
        count, decimal = divmod(decimal, number)
        result.append(numeral * count)
    return "".join(result)


def arabic(value):
    text = str(value).upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total_value = 0
    previous = 0
    for character in reversed(text):
        current = values[character]
        if current < previous:
            total_value -= current
        else:
            total_value += current
            previous = current
    return str(total_value)


def binary(value):
    return bin(int(value))[2:]


def octal(value):
    return oct(int(value))[2:]


def hex(value):
    return format(int(value), "x")


def base64(value):
    return _base64.b64encode(str(value).encode()).decode()


def polybius(value):
    alphabet = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
    positions = {
        character: f"{index // 5 + 1}{index % 5 + 1}"
        for index, character in enumerate(alphabet)
    }
    positions["J"] = positions["I"]
    return "".join(
        positions.get(character.upper(), character) for character in str(value)
    )


def rot13(value):
    result = []
    for character in str(value):
        if "a" <= character <= "z":
            result.append(chr((ord(character) - ord("a") + 13) % 26 + ord("a")))
        elif "A" <= character <= "Z":
            result.append(chr((ord(character) - ord("A") + 13) % 26 + ord("A")))
        else:
            result.append(character)
    return "".join(result)


_MORSE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
}


def morse(value):
    return " ".join(
        _MORSE.get(character.upper(), character) for character in str(value)
    )


def log(value):
    return math.log(float(value))


def log10(value):
    return math.log10(float(value))


def log2(value):
    return math.log2(float(value))


def sqrt(value):
    return math.sqrt(float(value))


def sin(value):
    return math.sin(float(value))


def cos(value):
    return math.cos(float(value))


def tan(value):
    return math.tan(float(value))


def asin(value):
    return math.asin(float(value))


def acos(value):
    return math.acos(float(value))


def atan(value):
    return math.atan(float(value))


def degrees(value):
    return math.degrees(float(value))


def radians(value):
    return math.radians(float(value))


def celcius(value):
    return (float(value) - 32) * 5 / 9


def fahrenheit(value):
    return float(value) * 9 / 5 + 32


def kelvin(value):
    return float(value) + 273.15


def imperial(value):
    return float(value) * 0.0393701


def metric(value):
    return float(value) * 25.4


def floor(value):
    return math.floor(float(value))


def ceil(value):
    return math.ceil(float(value))


def round(value):
    return _builtins.round(float(value))


def abs(value):
    return _builtins.abs(float(value))


def factorial(value):
    return math.factorial(int(value))


def isprime(value):
    number = int(value)
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False
    limit = math.isqrt(number)
    return all(number % divisor for divisor in range(3, limit + 1, 2))


def add(value, n):
    return float(value) + float(n)


def subtract(value, n):
    return float(value) - float(n)


def divide(value, n):
    return float(value) / float(n)


def negate(value):
    return -float(value)


def sign(value):
    number = float(value)
    if number == 0:
        return 0.0
    return 1.0 if number > 0 else -1.0


def lunar(value):
    try:
        import ephem
    except ImportError as exc:
        raise RuntimeError(
            "Astronomy support requires pip install sigils[astronomy]"
        ) from exc
    timestamp = _time.time() if not value else int(value)
    return str(ephem.Moon(ephem.Date(_time.gmtime(timestamp)[:6])).phase)


def search(value, substring):
    return str(substring) in str(value)


def length(value):
    return len(value)


def lines(value):
    return len(str(value).splitlines())


def words(value):
    return len(str(value).split())


def _numbers(value):
    return [float(number) for number in str(value).split(",")]


def average(value):
    numbers = _numbers(value)
    return _builtins.sum(numbers) / len(numbers)


def median(value):
    numbers = sorted(_numbers(value))
    middle = len(numbers) // 2
    if len(numbers) % 2:
        return numbers[middle]
    return (numbers[middle - 1] + numbers[middle]) / 2


def mode(value):
    numbers = _numbers(value)
    return _builtins.max(numbers, key=numbers.count)


def min(value):
    return _builtins.min(_numbers(value))


def max(value):
    return _builtins.max(_numbers(value))


def sum(value):
    return _builtins.sum(_numbers(value))


_TAROT_CARDS = (
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
    "Ace of Wands",
    "Two of Wands",
    "Three of Wands",
    "Four of Wands",
    "Five of Wands",
    "Six of Wands",
    "Seven of Wands",
    "Eight of Wands",
    "Nine of Wands",
    "Ten of Wands",
    "Page of Wands",
    "Knight of Wands",
    "Queen of Wands",
    "King of Wands",
    "Ace of Cups",
    "Two of Cups",
    "Three of Cups",
    "Four of Cups",
    "Five of Cups",
    "Six of Cups",
    "Seven of Cups",
    "Eight of Cups",
    "Nine of Cups",
    "Ten of Cups",
    "Page of Cups",
    "Knight of Cups",
    "Queen of Cups",
    "King of Cups",
    "Ace of Swords",
    "Two of Swords",
    "Three of Swords",
    "Four of Swords",
    "Five of Swords",
    "Six of Swords",
    "Seven of Swords",
    "Eight of Swords",
    "Nine of Swords",
    "Ten of Swords",
    "Page of Swords",
    "Knight of Swords",
    "Queen of Swords",
    "King of Swords",
    "Ace of Pentacles",
    "Two of Pentacles",
    "Three of Pentacles",
    "Four of Pentacles",
    "Five of Pentacles",
    "Six of Pentacles",
    "Seven of Pentacles",
    "Eight of Pentacles",
    "Nine of Pentacles",
    "Ten of Pentacles",
    "Page of Pentacles",
    "Knight of Pentacles",
    "Queen of Pentacles",
    "King of Pentacles",
)


def tarot(value):
    index = random.randint(0, len(_TAROT_CARDS) - 1) if not value else int(value)
    return _TAROT_CARDS[index]


def swapcase(value):
    return str(value).swapcase()


def isnumeric(value):
    return str(value).isnumeric()


def isalpha(value):
    return str(value).isalpha()


def isalnum(value):
    return str(value).isalnum()


def ord(value):
    return _builtins.ord(str(value))


def chr(value):
    return _builtins.chr(int(value))


def urlencode(value):
    return urllib.parse.quote_plus(str(value))


def urldecode(value):
    return urllib.parse.unquote_plus(str(value))


def hash(value, method="sha256"):
    digest = hashlib.new(str(method).lower())
    digest.update(str(value).encode())
    return digest.hexdigest()


def quote(value, quote_type="'"):
    return f"{quote_type}{value}{quote_type}"


def unquote(value):
    text = str(value)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def tetrad(value):
    symbols = ["D", "H", "C", "V"]
    if not value:
        return symbols
    return symbols[int(value) % 4]


def host(value):
    if not value or not isinstance(value, str):
        return socket.gethostname()
    try:
        return socket.gethostbyname(value)
    except socket.gaierror as exc:
        return f"Error looking up host {value!r}: {exc}"


def cwd(value):
    current = os.getcwd()
    if not value:
        return current
    for item in os.listdir(current):
        path = os.path.join(current, item)
        if os.path.isdir(path) and str(value) in item:
            return path
    return None


_TOOL_NAMES = (
    "lower",
    "upper",
    "trim",
    "slugify",
    "reverse",
    "capitalize",
    "title",
    "count",
    "replace",
    "first",
    "last",
    "before",
    "after",
    "between",
    "strip",
    "zfill",
    "env",
    "epoch",
    "sigil",
    "nth",
    "split",
    "month",
    "day",
    "year",
    "date",
    "time",
    "zodiac",
    "weekday",
    "rand",
    "randint",
    "choice",
    "shuffle",
    "sample",
    "join",
    "sort",
    "hide",
    "mask",
    "truncate",
    "pad",
    "scramble",
    "tag",
    "link",
    "image",
    "style",
    "script",
    "html",
    "json",
    "toml",
    "yaml",
    "markdown",
    "multiply",
    "roman",
    "arabic",
    "binary",
    "octal",
    "hex",
    "base64",
    "polybius",
    "rot13",
    "morse",
    "log",
    "log10",
    "log2",
    "sqrt",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "degrees",
    "radians",
    "celcius",
    "fahrenheit",
    "kelvin",
    "imperial",
    "metric",
    "floor",
    "ceil",
    "round",
    "abs",
    "factorial",
    "isprime",
    "add",
    "subtract",
    "divide",
    "negate",
    "sign",
    "lunar",
    "search",
    "length",
    "lines",
    "words",
    "average",
    "median",
    "mode",
    "min",
    "max",
    "sum",
    "tarot",
    "swapcase",
    "isnumeric",
    "isalpha",
    "isalnum",
    "ord",
    "chr",
    "urlencode",
    "urldecode",
    "hash",
    "quote",
    "unquote",
    "tetrad",
    "host",
    "cwd",
)

tools = {name: globals()[name] for name in _TOOL_NAMES}
tools["tools"] = tools

__all__ = [*_TOOL_NAMES, "tools"]
