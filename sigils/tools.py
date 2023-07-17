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

def lower(input_string):
    """Converts a string to lowercase."""
    return input_string.lower()

def upper(input_string):
    """Converts a string to uppercase."""
    return input_string.upper()

def trim(input_string):
    """Removes leading and trailing whitespace from a string."""
    return input_string.strip()

def slugify(input_string):
    """Converts a string to a 'slug' suitable for use in URLs."""
    return input_string.lower().replace(" ", "-")

def reverse(input_string):
    """Reverses a string or list."""
    if ',' in input_string:
        return ','.join(input_string.split(',')[::-1])
    return input_string[::-1]

def capitalize(input_string):
    """Capitalizes the first character of a string."""
    return input_string.capitalize()

def title(input_string):
    """Converts a string to title case."""
    return input_string.title()
    
def count(input_string, substring):
    """Counts the occurrences of a substring in a string."""
    return input_string.count(substring)

def replace(input_string, old, new):
    """Replaces all occurrences of a substring with another substring."""
    return input_string.replace(old, new)

def first(input_string, n='1'):
    """Returns the first n characters of a string."""
    return input_string[:int(n)]

def last(input_string, n='1'):
    """Returns the last n characters of a string."""
    return input_string[-int(n):]

def before(input_string, substring):
    """Returns the part of a string before a substring."""
    return input_string.split(substring)[0]

def after(input_string, substring):
    """Returns the part of a string after a substring."""
    return input_string.split(substring)[1]

def between(input_string, start, end):
    """Returns the part of a string between two substrings."""
    return input_string.split(start)[1].split(end)[0]

def strip(input_string, substring):
    """Removes all occurrences of a substring from a string."""
    return input_string.replace(substring, '')

def zfill(input_string, n):
    """Pads a string with zeros until it reaches a specified length."""
    return input_string.zfill(int(n))

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

def env(input_string):
    """Returns the value of an environment variable."""
    if input_string is None:
        return ''
    # Avoid secrets in the environment. This is not a complete list.
    for forbidden in FORBIDDEN_ENV:
        if forbidden in input_string.upper():
            return ''
    return os.environ.get(input_string.upper())

def epoch(input_string=None):
    """Return server time in seconds since the epoch."""
    return str(time.time())

# Wrap the input in a %[sigil]
def sigil(input_string, sigil_start='%[', sigil_end=']'):
    """Wraps a string in a sigil, or any other string."""
    return f"{sigil_start}{input_string}{sigil_end}"

# List available sigils (one level deep), separated by a comma
def sigils(input_string):
    """Returns a comma-separated list of available sigils."""
    return ','.join([f"%[{key}]" for key in Sigil(input_string).sigils()])

# Treat as a list separated by a delimiter (Comma by default) and get the nth item
def nth(input_string, n, delimiter=','):
    """Returns the nth item in a list."""
    return input_string.split(delimiter)[int(n)]

def split(input_string, input_delimiter=',', output_delimiter=','):
    """Splits a string into a list. Returns the list separated by a delimiter (comma by default)."""
    return output_delimiter.join(input_string.split(input_delimiter))

def month(input_string=None):
    """Returns the name of a month from a month number or current month."""
    if input_string is None:
        return calendar.month_name[time.localtime().tm_mon]
    return calendar.month_name[int(input_string)]

def day(input_string=None):
    """Returns the name of a day from a day number or current day."""
    if input_string is None:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[int(input_string)]

def year(input_string=None):
    """Returns the current year or the year from a timestamp."""
    if input_string is None:
        return str(time.localtime().tm_year)
    return str(time.localtime(int(input_string)).tm_year)

def date(input_string=None, format='%Y-%m-%d'):
    """Returns the current date or the date from a timestamp."""
    if input_string is None:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(input_string)))

def time(input_string=None, format='%H:%M:%S'):
    """Returns the current time or the time from a timestamp."""
    if input_string is None:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(input_string)))

def zodiac(input_string=None):
    """Returns the zodiac sign for the current date or the date from a timestamp."""
    if input_string is None:
        month = time.localtime().tm_mon
        day = time.localtime().tm_mday
    else:
        month = time.localtime(int(input_string)).tm_mon
        day = time.localtime(int(input_string)).tm_mday
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

def weekday(input_string=None):
    """Returns the weekday for the current date or the date from a timestamp."""
    if input_string is None:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[time.localtime(int(input_string)).tm_wday]

def rand(input_string=None):
    """Returns a random number between 0 and 1."""
    if input_string is None:
        return str(random.random())
    return str(random.random() * float(input_string))

def randint(input_string):
    """Returns a random integer between 0 and the input number."""
    return str(random.randint(0, int(input_string)))

def choice(input_string):
    """Returns a random item from a list."""
    return random.choice(input_string.split(','))

def shuffle(input_string):
    """Returns a shuffled list."""
    items = input_string.split(',')
    random.shuffle(items)
    return ','.join(items)

def sample(input_string, n='1'):
    """Returns n random items from a list."""
    items = input_string.split(',')
    random.shuffle(items)
    return ','.join(items[:int(n)])

def join(input_string, delimiter=','):
    """Joins a list into a string, separated by a delimiter."""
    return delimiter.join(input_string.split(','))

def sort(input_string):
    """Sorts a list."""
    items = input_string.split(',')
    items.sort()
    return ','.join(items)

def hide(input_string):
    """Hides a string by replacing it with asterisks."""
    return '*' * len(input_string)

def mask(input_string, n='4'):
    """Masks a string by replacing all but the last n characters with asterisks."""
    return '*' * (len(input_string) - int(n)) + input_string[-int(n):]

def truncate(input_string, n='50', ellipsis='...'):
    """Truncates a string to a specified length and adds an ellipsis."""
    return input_string[:int(n)] + ellipsis

def pad(input_string, n='50', character=' '):
    """Pads a string to a specified length with a specified character."""
    return input_string.ljust(int(n), character)

def scramble(input_string):
    """Scrambles the characters in a string."""
    items = list(input_string)
    random.shuffle(items)
    return ''.join(items)

def tag(input_string, tag='div', attributes=''):
    """Wraps a string in an HTML tag."""
    return f"<{tag} {attributes}>{input_string}</{tag}>"

def link(input_string, url):
    """Wraps a string in an HTML link."""
    return f'<a href="{url}">{input_string}</a>'

def image(input_string, url):
    """Wraps a string in an HTML image."""
    return f'<img src="{url}" alt="{input_string}">'

def style(input_string, style):
    """Wraps a string in an HTML style tag."""
    return f'<style>{style}</style>{input_string}'

def script(input_string, script):
    """Wraps a string in an HTML script tag."""
    return f'<script>{script}</script>{input_string}'

def html(input_string):
    """Escapes HTML characters."""
    return input_string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def json(input_string, target=None):
    """Converts a JSON string to a Python dictionary."""
    import json
    if target is None:
        return json.loads(input_string)
    return json.loads(input_string)[target]

def toml(input_string, target=None):
    """Converts a TOML string to a Python dictionary."""
    try:
        import toml
    except ImportError:
        import tomllib as toml
    if target is None:
        return toml.loads(input_string)
    return toml.loads(input_string)[target]

def yaml(input_string, target=None):
    """Converts a YAML string to a Python dictionary."""
    import yaml
    if target is None:
        return yaml.safe_load(input_string)
    return yaml.safe_load(input_string)[target]

def markdown(input_string):
    """Converts a Markdown string to HTML."""
    import markdown
    return markdown.markdown(input_string)

def multiply(input_string, n):
    """Multiplies a string by a number."""
    # If input_string looks like a number do an actual multiplication
    if input_string.replace('.', '', 1).isdigit():
        return str(float(input_string) * float(n))
    return input_string * int(n)

def roman(input_string):
    """Converts an integer to a Roman numeral."""
    decimal = int(input_string)
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

def arabic(input_string):
    """Converts a Roman numeral to an integer."""
    roman = input_string.upper()
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

def binary(input_string):
    """Converts an integer to a binary string."""
    return bin(int(input_string))[2:]

def octal(input_string):
    """Converts an integer to an octal string."""
    return oct(int(input_string))[2:]

def hex(input_string):
    """Converts an integer to a hexadecimal string."""
    return hex(int(input_string))[2:]

def base64(input_string):
    """Converts a string to a base64 string."""
    import base64
    return base64.b64encode(input_string.encode()).decode()

def polybius(input_string):
    """Converts a string to a polybius cipher."""
    polybius_square = {
        'A': '11', 'B': '12', 'C': '13', 'D': '14', 'E': '15', 'F': '21', 'G': '22', 'H': '23', 'I': '24', 'J': '24', 'K': '25', 'L': '31', 'M': '32', 'N': '33', 'O': '34', 'P': '35', 'Q': '41', 'R': '42', 'S': '43', 'T': '44', 'U': '45', 'V': '51', 'W': '52', 'X': '53', 'Y': '54', 'Z': '55'
    }
    return ''.join([polybius_square.get(char.upper(), char) for char in input_string])

def rot13(input_string):
    """Converts a string to a rot13 cipher."""
    rot13_square = {
        'A': 'N', 'B': 'O', 'C': 'P', 'D': 'Q', 'E': 'R', 'F': 'S', 'G': 'T', 'H': 'U', 'I': 'V', 'J': 'W', 'K': 'X', 'L': 'Y', 'M': 'Z', 'N': 'A', 'O': 'B', 'P': 'C', 'Q': 'D', 'R': 'E', 'S': 'F', 'T': 'G', 'U': 'H', 'V': 'I', 'W': 'J', 'X': 'K', 'Y': 'L', 'Z': 'M'
    }
    return ''.join([rot13_square.get(char.upper(), char) for char in input_string])

def morse(input_string):
    """Converts a string to a morse code."""
    morse_square = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..'
    }
    return ' '.join([morse_square.get(char.upper(), char) for char in input_string])

def log(input_string):
    """Returns the natural logarithm of a number."""
    import math
    return str(math.log(float(input_string)))

def log10(input_string):
    """Returns the base-10 logarithm of a number."""
    import math
    return str(math.log10(float(input_string)))

def log2(input_string):
    """Returns the base-2 logarithm of a number."""
    import math
    return str(math.log2(float(input_string)))

def sqrt(input_string):
    """Returns the square root of a number."""
    import math
    return str(math.sqrt(float(input_string)))

def sin(input_string):
    """Returns the sine of a number."""
    import math
    return str(math.sin(float(input_string)))

def cos(input_string):
    """Returns the cosine of a number."""
    import math
    return str(math.cos(float(input_string)))

def tan(input_string):
    """Returns the tangent of a number."""
    import math
    return str(math.tan(float(input_string)))

def asin(input_string):
    """Returns the arcsine of a number."""
    import math
    return str(math.asin(float(input_string)))

def acos(input_string):
    """Returns the arccosine of a number."""
    import math
    return str(math.acos(float(input_string)))

def atan(input_string):
    """Returns the arctangent of a number."""
    import math
    return str(math.atan(float(input_string)))

def degrees(input_string):
    """Converts radians to degrees."""
    import math
    return str(math.degrees(float(input_string)))

def radians(input_string):
    """Converts degrees to radians."""
    import math
    return str(math.radians(float(input_string)))

def celcius(input_string):
    """Converts Fahrenheit to Celcius."""
    return str((float(input_string) - 32) * 5 / 9)

def fahrenheit(input_string):
    """Converts Celcius to Fahrenheit."""
    return str(float(input_string) * 9 / 5 + 32)

def kelvin(input_string):
    """Converts Celcius to Kelvin."""
    return str(float(input_string) + 273.15)

def imperial(input_string):
    """Converts metric units to imperial units."""
    return str(float(input_string) * 0.0393701)

def metric(input_string):
    """Converts imperial units to metric units."""
    return str(float(input_string) * 25.4)

def floor(input_string):
    """Rounds a number down to the nearest integer."""
    import math
    return str(math.floor(float(input_string)))

def ceil(input_string):
    """Rounds a number up to the nearest integer."""
    import math
    return str(math.ceil(float(input_string)))

def round(input_string):
    """Rounds a number to the nearest integer."""
    return str(int(float(input_string) + 0.5))

def abs(input_string):
    """Returns the absolute value of a number."""
    import math
    return str(math.fabs(float(input_string)))

def factorial(input_string):
    """Returns the factorial of a number."""
    import math
    return str(math.factorial(int(input_string)))

def isprime(input_string):
    """Returns True if a number is prime, False otherwise."""
    import math
    return str(math.isprime(int(input_string)))

def add(input_string, n):
    """Adds a number to a number."""
    return str(float(input_string) + float(n))

def subtract(input_string, n):
    """Subtracts a number from a number."""
    return str(float(input_string) - float(n))

def divide(input_string, n):
    """Divides a number by a number."""
    return str(float(input_string) / float(n))

def negate(input_string):
    """Negates a number."""
    return str(-float(input_string))

def sign(input_string):
    """Returns the sign of a number."""
    return str(float(input_string) / abs(float(input_string)))

def lunar(input_string=None):
    """Returns the current lunar phase or the lunar phase from a timestamp."""
    if input_string is None:
        timestamp = time.time()
    else:
        timestamp = int(input_string)
    import ephem
    moon = ephem.Moon(timestamp)
    return str(moon.phase)

def search(input_string, substring):
    """Returns True if a substring is found in a string, False otherwise."""
    return str(substring in input_string)

def length(input_string):
    """Returns the length of a string."""
    return str(len(input_string))

def lines(input_string):
    """Returns the number of lines in a string."""
    return str(len(input_string.split('\n')))

def words(input_string):
    """Returns the number of words in a string."""
    return str(len(input_string.split()))

def average(input_string):
    """Returns the average of a list of numbers."""
    return str(sum([float(num) for num in input_string.split(',')]) / len(input_string.split(',')))

def median(input_string):
    """Returns the median of a list of numbers."""
    items = [float(num) for num in input_string.split(',')]
    items.sort()
    if len(items) % 2 == 0:
        return str((items[len(items) // 2 - 1] + items[len(items) // 2]) / 2)
    return str(items[len(items) // 2])

def mode(input_string):
    """Returns the mode of a list of numbers."""
    items = [float(num) for num in input_string.split(',')]
    items.sort()
    max_count = 0
    max_item = None
    for item in items:
        count = items.count(item)
        if count > max_count:
            max_count = count
            max_item = item
    return str(max_item)

def min(input_string):
    """Returns the minimum of a list of numbers."""
    items = [float(num) for num in input_string.split(',')]
    return str(min(items))

def max(input_string):
    """Returns the maximum of a list of numbers."""
    items = [float(num) for num in input_string.split(',')]
    return str(max(items))

def sum(input_string):
    """Returns the sum of a list of numbers."""
    items = [float(num) for num in input_string.split(',')]
    return str(sum(items))

def tarot(input_string=None):
    if input_string is None:
        num = random.randint(0, 77)
    else:
        num = int(input_string)
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

def swapcase(input_string):
    """Swaps case of each character in the input string."""
    return input_string.swapcase()

def isnumeric(input_string):
    """Checks if the input string is numeric."""
    return str(input_string.isnumeric())

def isalpha(input_string):
    """Checks if the input string contains only alphabetic characters."""
    return str(input_string.isalpha())

def isalnum(input_string):
    """Checks if the input string contains only alphanumeric characters."""
    return str(input_string.isalnum())

def ord(input_string):
    """Converts a character to its Unicode code point."""
    return str(ord(input_string))

def chr(input_string):
    """Converts a Unicode code point to its corresponding character."""
    return chr(int(input_string))

def urlencode(input_string):
    """URL-encodes the input string."""
    return urllib.parse.quote_plus(input_string)

def urldecode(input_string):
    """URL-decodes the input string."""
    return urllib.parse.unquote_plus(input_string)

def hash(input_string, method='sha256'):
    """Hashes the input string using the specified hash method."""
    if method == 'md5':
        return hashlib.md5(input_string.encode()).hexdigest()
    elif method == 'sha1':
        return hashlib.sha1(input_string.encode()).hexdigest()
    elif method == 'sha512':
        return hashlib.sha512(input_string.encode()).hexdigest()
    else:  # default to 'sha256'
        return hashlib.sha256(input_string.encode()).hexdigest()

def quote(input_string, quote_type="'"):
    """Adds quotes around a string."""
    return f"{quote_type}{input_string}{quote_type}"

def unquote(input_string):
    """Removes quotes around a string if present."""
    if (input_string.startswith("'") and input_string.endswith("'")) or (input_string.startswith('"') and input_string.endswith('"')):
        return input_string[1:-1]
    return input_string


tools = {name: obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isfunction(obj)}
