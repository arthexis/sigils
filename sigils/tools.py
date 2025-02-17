import os
import time
import calendar
import random
import hashlib
import urllib.parse
import inspect
import sys

# Tools available at the default context level
# Note that all functions take strings as input and return strings as output
# For some functions its ok if the input is None, but output will always be a string

def lower(target):
    """Converts a string to lowercase."""
    return str(target).lower()

def upper(target):
    """Converts a string to uppercase."""
    return str(target).upper()

def trim(target):
    """Removes leading and trailing whitespace from a string."""
    return target.strip()

def slugify(target):
    """Converts a string to a 'slug' suitable for use in URLs."""
    return target.lower().replace(" ", "-")

def reverse(target):
    """Reverses a string or list."""
    if ',' in target:
        return ','.join(target.split(',')[::-1])
    return target[::-1]

def capitalize(target):
    """Capitalizes the first character of a string."""
    return target.capitalize()

def title(target):
    """Converts a string to title case."""
    return target.title()
    
def count(target, substring):
    """Counts the occurrences of a substring in a string."""
    return target.count(substring)

def replace(target, old, new):
    """Replaces all occurrences of a substring with another substring."""
    return target.replace(old, new)

def first(target, n='1'):
    """Returns the first n characters of a string."""
    return target[:int(n)]

def last(target, n='1'):
    """Returns the last n characters of a string."""
    return target[-int(n):]

def before(target, substring):
    """Returns the part of a string before a substring."""
    return target.split(substring)[0]

def after(target, substring):
    """Returns the part of a string after a substring."""
    return target.split(substring)[1]

def between(target, start, end):
    """Returns the part of a string between two substrings."""
    return target.split(start)[1].split(end)[0]

def strip(target, substring):
    """Removes all occurrences of a substring from a string."""
    return target.replace(substring, '')

def zfill(target, n):
    """Pads a string with zeros until it reaches a specified length."""
    return target.zfill(int(n))

FORBIDDEN_ENV = [
    'DATABASE',
    'KEY',
    'SECRET',
    'ACCESS_TOKEN',
    'AWS',
    'SSH',
    'OAUTH',
    'SMTP',
    'CREDENTIALS',
    'ENV_FILE',
    'SESSION'
]

def env(target):
    """Returns the value of an environment variable."""
    if not target:
        return dict(os.environ)
    target = str(target)
    # Avoid secrets in the environment. This is not a complete list.
    for forbidden in FORBIDDEN_ENV:
        if forbidden in target.upper():
            return ''
    return os.environ.get(target.upper())

def epoch(target):
    """Return server time in seconds since the epoch."""
    if target:
        return time.time() - int(target)
    return time.time()

# Wrap the input in a %[sigil]
def sigil(target, start='%[', end=']'):
    """Wraps a string in a sigil, or any other string."""
    return f"{start}{target}{end}"

# List available sigils (one level deep), separated by a comma
def sigils(target):
    """Returns a comma-separated list of available sigils."""
    return ','.join([f"%[{key}]" for key in Sigil(target).sigils()])

# Treat as a list separated by a delimiter (Comma by default) and get the nth item
def nth(target, n, delimiter=','):
    """Returns the nth item in a list."""
    return target.split(delimiter)[int(n)]

def split(target, delimiter=',', separator=','):
    """Splits a string into a list. Returns the list separated by a delimiter (comma by default)."""
    return separator.join(target.split(delimiter))

def month(target=None):
    """Returns the name of a month from a month number or current month."""
    if target is None:
        return calendar.month_name[time.localtime().tm_mon]
    return calendar.month_name[int(target)]

def day(target=None):
    """Returns the name of a day from a day number or current day."""
    if target is None:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[int(target)]

def year(target=None):
    """Returns the current year or the year from a timestamp."""
    if target is None:
        return time.localtime().tm_year
    return time.localtime(int(target)).tm_year

def date(target=None, format='%Y-%m-%d'):
    """Returns the current date or the date from a timestamp."""
    if target is None:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(target)))

def time(target=None, format='%H:%M:%S'):
    """Returns the current time or the time from a timestamp."""
    if target is None:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(target)))

def zodiac(target=None):
    """Returns the zodiac sign for the current date or the date from a timestamp."""
    if target is None:
        month = time.localtime().tm_mon
        day = time.localtime().tm_mday
    else:
        month = time.localtime(int(target)).tm_mon
        day = time.localtime(int(target)).tm_mday
    if (month == 12 and day >= 22) or (month == 1 and day <= 19):
        return "Capricorn"
    elif (month == 1 and day >= 20) or (month == 2 and day <= 17):
        return "Aquarius"
    elif (month == 2 and day >= 18) or (month == 3 and day <= 19):
        return "Pisces"
    elif (month == 3 and day >= 20) or (month == 4 and day <= 19):
        return "Aries"
    elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
        return "Taurus"
    elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
        return "Gemini"
    elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
        return "Cancer"
    elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
        return "Leo"
    elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
        return "Virgo"
    elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
        return "Libra"
    elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
        return "Scorpio"
    elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
        return "Sagittarius"
    else:
        return ""

def weekday(target):
    """Returns the weekday for the current date or the date from a timestamp."""
    if not target:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[time.localtime(int(target)).tm_wday]

def rand(target):
    """Returns a random number between 0 and 1."""
    if not target:
        return random.random()
    return random.random() * float(target)


def randint(target):
    """Returns a random integer between 0 and the input number."""
    return str(random.randint(0, int(target)))

def choice(target):
    """Returns a random item from a list."""
    return random.choice(target.split(','))

def shuffle(target):
    """Returns a shuffled list."""
    items = target.split(',')
    random.shuffle(items)
    return ','.join(items)

def sample(target, n='1'):
    """Returns n random items from a list."""
    items = target.split(',')
    random.shuffle(items)
    return ','.join(items[:int(n)])

def join(target, delimiter=','):
    """Joins a list into a string, separated by a delimiter."""
    return delimiter.join(target.split(','))

def sort(target):
    """Sorts a list."""
    items = target.split(',')
    items.sort()
    return ','.join(items)

def hide(target):
    """Hides a string by replacing it with asterisks."""
    return '*' * len(target)

def mask(target, n='4'):
    """Masks a string by replacing all but the last n characters with asterisks."""
    return '*' * (len(target) - int(n)) + target[-int(n):]

def truncate(target, n='50', ellipsis='...'):
    """Truncates a string to a specified length and adds an ellipsis."""
    return target[:int(n)] + ellipsis

def pad(target, n='50', character=' '):
    """Pads a string to a specified length with a specified character."""
    return target.ljust(int(n), character)

def scramble(target):
    """Scrambles the characters in a string."""
    items = list(target)
    random.shuffle(items)
    return ''.join(items)

def tag(target, tag='div', attributes=''):
    """Wraps a string in an HTML tag."""
    return f"<{tag} {attributes}>{target}</{tag}>"

def link(target, url):
    """Wraps a string in an HTML link."""
    return f'<a href="{url}">{target}</a>'

def image(target, url):
    """Wraps a string in an HTML image."""
    return f'<img src="{url}" alt="{target}">'

def style(target, style):
    """Wraps a string in an HTML style tag."""
    return f'<style>{style}</style>{target}'

def script(target, script):
    """Wraps a string in an HTML script tag."""
    return f'<script>{script}</script>{target}'

def html(target):
    """Escapes HTML characters."""
    return target.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def json(target, index=None):
    """Converts a JSON string to a Python dictionary."""
    import json
    if target is None:
        return json.loads(target)
    return json.loads(target)[index]

def toml(target, v=None):
    """Converts a TOML string to a Python dictionary."""
    try:
        import toml
    except ImportError:
        import tomllib as toml
    if target is None:
        return toml.loads(target)
    return toml.loads(target)[index]

def yaml(target, index=None):
    """Converts a YAML string to a Python dictionary."""
    import yaml
    if target is None:
        return yaml.safe_load(target)
    return yaml.safe_load(target)[index]

def markdown(target):
    """Converts a Markdown string to HTML."""
    import markdown
    return markdown.markdown(target)

def multiply(target, n):
    """Multiplies a string by a number."""
    # If target looks like a number do an actual multiplication
    if target.replace('.', '', 1).isdigit():
        return str(float(target) * float(n))
    return target * int(n)

def roman(target):
    """Converts an integer to a Roman numeral."""
    decimal = int(target)
    if decimal == 0:
        return '0'
    if decimal < 0:
        return '-' + roman(str(-decimal))
    result = ''
    for (num, rom) in zip([1000, 900, 500, 400, 100, 90, 50, 40, 10, 9 ,5, 4, 1],
                            ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX' ,'V', 'IV', 'I']):
            result += rom * (decimal // num)
            decimal %= num
    return result

def arabic(target):
    """Converts a Roman numeral to an integer."""
    roman = target.upper()
    roman_nums = {'M': 1000, 'CM': 900, 'D': 500, 'CD': 400, 'C': 100,
                'XC': 90, 'L': 50, 'XL': 40, 'X': 10, 'IX': 9,
                'V': 5, 'IV': 4, 'I': 1}
    arabic = 0
    for i in range(len(roman)):
        if i > 0 and roman_nums[roman[i]] > roman_nums[roman[i - 1]]:
            arabic += roman_nums[roman[i]] - 2 * roman_nums[roman[i - 1]]
        else:
            arabic += roman_nums[roman[i]]
    return str(arabic)

def binary(target):
    """Converts an integer to a binary string."""
    return bin(int(target))[2:]

def octal(target):
    """Converts an integer to an octal string."""
    return oct(int(target))[2:]

def hex(target):
    """Converts an integer to a hexadecimal string."""
    return hex(int(target))[2:]

def base64(target):
    """Converts a string to a base64 string."""
    import base64
    return base64.b64encode(target.encode()).decode()

def polybius(target):
    """Converts a string to a polybius cipher."""
    polybius_square = {
        'A': '11', 'B': '12', 'C': '13', 'D': '14', 'E': '15', 'F': '21', 'G': '22', 'H': '23', 'I': '24', 'J': '24', 'K': '25', 'L': '31', 'M': '32', 'N': '33', 'O': '34', 'P': '35', 'Q': '41', 'R': '42', 'S': '43', 'T': '44', 'U': '45', 'V': '51', 'W': '52', 'X': '53', 'Y': '54', 'Z': '55'
    }
    return ''.join([polybius_square.get(char.upper(), char) for char in target])

def rot13(target):
    """Converts a string to a rot13 cipher."""
    rot13_square = {
        'A': 'N', 'B': 'O', 'C': 'P', 'D': 'Q', 'E': 'R', 'F': 'S', 'G': 'T', 'H': 'U', 'I': 'V', 'J': 'W', 'K': 'X', 'L': 'Y', 'M': 'Z', 'N': 'A', 'O': 'B', 'P': 'C', 'Q': 'D', 'R': 'E', 'S': 'F', 'T': 'G', 'U': 'H', 'V': 'I', 'W': 'J', 'X': 'K', 'Y': 'L', 'Z': 'M'
    }
    return ''.join([rot13_square.get(char.upper(), char) for char in target])

def morse(target):
    """Converts a string to a morse code."""
    morse_square = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..'
    }
    return ' '.join([morse_square.get(char.upper(), char) for char in target])

def log(target):
    """Returns the natural logarithm of a number."""
    import math
    return math.log(float(target))

def log10(target):
    """Returns the base-10 logarithm of a number."""
    import math
    return math.log10(float(target))

def log2(target):
    """Returns the base-2 logarithm of a number."""
    import math
    return math.log2(float(target))

def sqrt(target):
    """Returns the square root of a number."""
    import math
    return math.sqrt(float(target))

def sin(target):
    """Returns the sine of a number."""
    import math
    return math.sin(float(target))

def cos(target):
    """Returns the cosine of a number."""
    import math
    return math.cos(float(target))

def tan(target):
    """Returns the tangent of a number."""
    import math
    return math.tan(float(target))

def asin(target):
    """Returns the arcsine of a number."""
    import math
    return math.asin(float(target))

def acos(target):
    """Returns the arccosine of a number."""
    import math
    return math.acos(float(target))

def atan(target):
    """Returns the arctangent of a number."""
    import math
    return math.atan(float(target))

def degrees(target):
    """Converts radians to degrees."""
    import math
    return math.degrees(float(target))

def radians(target):
    """Converts degrees to radians."""
    import math
    return math.radians(float(target))

def celcius(target):
    """Converts Fahrenheit to Celcius."""
    return (float(target) - 32) * 5 / 9

def fahrenheit(target):
    """Converts Celcius to Fahrenheit."""
    return float(target) * 9 / 5 + 32

def kelvin(target):
    """Converts Celcius to Kelvin."""
    return float(target) + 273.15

def imperial(target):
    """Converts metric units to imperial units."""
    return float(target) * 0.0393701

def metric(target):
    """Converts imperial units to metric units."""
    return float(target) * 25.4

def floor(target):
    """Rounds a number down to the nearest integer."""
    import math
    return math.floor(float(target))

def ceil(target):
    """Rounds a number up to the nearest integer."""
    import math
    return math.ceil(float(target))

def round(target):
    """Rounds a number to the nearest integer."""
    return int(float(target) + 0.5)

def abs(target):
    """Returns the absolute value of a number."""
    import math
    return math.fabs(float(target))

def factorial(target):
    """Returns the factorial of a number."""
    import math
    return math.factorial(int(target))

def isprime(target):
    """Returns True if a number is prime, False otherwise."""
    import math
    return math.isprime(int(target))

def add(target, n):
    """Adds a number to a number."""
    return float(target) + float(n)

def subtract(target, n):
    """Subtracts a number from a number."""
    return float(target) - float(n)

def divide(target, n):
    """Divides a number by a number."""
    return float(target) / float(n)

def negate(target):
    """Negates a number."""
    return -float(target)

def sign(target):
    """Returns the sign of a number."""
    return float(target) / abs(float(target))

def lunar(target=None):
    """Returns the current lunar phase or the lunar phase from a timestamp."""
    if target is None:
        timestamp = time.time()
    else:
        timestamp = int(target)
    import ephem
    moon = ephem.Moon(timestamp)
    return str(moon.phase)

def search(target, substring):
    """Returns True if a substring is found in a string, False otherwise."""
    return substring in target

def length(target):
    """Returns the length of a string or list."""
    return len(target)

def lines(target):
    """Returns the number of lines in a string."""
    return len(target.split('\n'))

def words(target):
    """Returns the number of words in a string."""
    return len(target.split())

def average(target):
    """Returns the average of a list of numbers."""
    return sum([float(num) for num in target.split(',')]) / len(target.split(','))

def median(target):
    """Returns the median of a list of numbers."""
    items = [float(num) for num in target.split(',')]
    items.sort()
    if len(items) % 2 == 0:
        return str((items[len(items) // 2 - 1] + items[len(items) // 2]) / 2)
    return items[len(items) // 2]

def mode(target):
    """Returns the mode of a list of numbers."""
    items = [float(num) for num in target.split(',')]
    items.sort()
    max_count = 0
    max_item = None
    for item in items:
        count = items.count(item)
        if count > max_count:
            max_count = count
            max_item = item
    return max_item

def min(target):
    """Returns the minimum of a list of numbers."""
    items = [float(num) for num in target.split(',')]
    return min(items)

def max(target):
    """Returns the maximum of a list of numbers."""
    items = [float(num) for num in target.split(',')]
    return max(items)

def sum(target):
    """Returns the sum of a list of numbers."""
    items = [float(num) for num in target.split(',')]
    return sum(items)

def tarot(target=None):
    if target is None:
        num = random.randint(0, 77)
    else:
        num = int(target)
    tarot_cards = [
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
        "King of Pentacles"
    ]
    return tarot_cards[num]

def swapcase(target):
    """Swaps case of each character in the input string."""
    return target.swapcase()

def isnumeric(target):
    """Checks if the input string is numeric."""
    return target.isnumeric()

def isalpha(target):
    """Checks if the input string contains only alphabetic characters."""
    return target.isalpha()

def isalnum(target):
    """Checks if the input string contains only alphanumeric characters."""
    return target.isalnum()

def ord(target):
    """Converts a character to its Unicode code point."""
    return ord(target)

def chr(target):
    """Converts a Unicode code point to its corresponding character."""
    return int(target)

def urlencode(target):
    """URL-encodes the input string."""
    return urllib.parse.quote_plus(target)

def urldecode(target):
    """URL-decodes the input string."""
    return urllib.parse.unquote_plus(target)

def hash(target, method='sha256'):
    """Hashes the input string using the specified hash method."""
    if method == 'md5':
        return hashlib.md5(target.encode()).hexdigest()
    elif method == 'sha1':
        return hashlib.sha1(target.encode()).hexdigest()
    elif method == 'sha512':
        return hashlib.sha512(target.encode()).hexdigest()
    else:  # default to 'sha256'
        return hashlib.sha256(target.encode()).hexdigest()

def quote(target, quote_type="'"):
    """Adds quotes around a string."""
    return f"{quote_type}{target}{quote_type}"

def unquote(target):
    """Removes quotes around a string if present."""
    if (target.startswith("'") and target.endswith("'")) or (target.startswith('"') and target.endswith('"')):
        return target[1:-1]
    return target

def tetrad(target):
    T = ["D", "H", "C", "V"]
    if not target:
        return T
    return T[int(target) % 4]

    

# Gather all the tools in one place
tools = {name: obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isfunction(obj)}
tools["tools"] = tools
