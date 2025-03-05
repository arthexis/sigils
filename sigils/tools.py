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

def lower(x):
    """Converts a string to lowercase."""
    return str(x).lower()

def upper(x):
    """Converts a string to uppercase."""
    return str(x).upper()

def trim(x):
    """Removes leading and trailing whitespace from a string."""
    return x.strip()

def slugify(x):
    """Converts a string to a 'slug' suitable for use in URLs."""
    return x.lower().replace(" ", "-")

def reverse(x):
    """Reverses a string or list."""
    if ',' in x:
        return ','.join(x.split(',')[::-1])
    return x[::-1]

def capitalize(x):
    """Capitalizes the first character of a string."""
    return x.capitalize()

def title(x):
    """Converts a string to title case."""
    return x.title()
    
def count(x, substring):
    """Counts the occurrences of a substring in a string."""
    return x.count(substring)

def replace(x, old, new):
    """Replaces all occurrences of a substring with another substring."""
    return x.replace(old, new)

def first(x, n='1'):
    """Returns the first n characters of a string."""
    return x[:int(n)]

def last(x, n='1'):
    """Returns the last n characters of a string."""
    return x[-int(n):]

def before(x, substring):
    """Returns the part of a string before a substring."""
    return x.split(substring)[0]

def after(x, substring):
    """Returns the part of a string after a substring."""
    return x.split(substring)[1]

def between(x, start, end):
    """Returns the part of a string between two substrings."""
    return x.split(start)[1].split(end)[0]

def strip(x, substring):
    """Removes all occurrences of a substring from a string."""
    return x.replace(substring, '')

def zfill(x, n):
    """Pads a string with zeros until it reaches a specified length."""
    return x.zfill(int(n))

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

def env(x):
    """Returns the value of an environment variable."""
    if not x:
        return dict(os.environ)
    x = str(x)
    # Avoid secrets in the environment. This is not a complete list.
    for forbidden in FORBIDDEN_ENV:
        if forbidden in x.upper():
            return ''
    return os.environ.get(x.upper())

def epoch(x):
    """Return server time in seconds since the epoch."""
    if x:
        return time.time() - int(x)
    return time.time()

# Wrap the input in a %[sigil]
def sigil(x, start='%[', end=']'):
    """Wraps a string in a sigil, or any other string."""
    return f"{start}{x}{end}"

# List available sigils (one level deep), separated by a comma
def sigils(x):
    """Returns a comma-separated list of available sigils."""
    return ','.join([f"%[{key}]" for key in Sigil(x).sigils()])

# Treat as a list separated by a delimiter (Comma by default) and get the nth item
def nth(x, n, delimiter=','):
    """Returns the nth item in a list."""
    return x.split(delimiter)[int(n)]

def split(x, delimiter=',', separator=','):
    """Splits a string into a list. Returns the list separated by a delimiter (comma by default)."""
    return separator.join(x.split(delimiter))

def month(x):
    """Returns the name of a month from a month number or current month."""
    if not x:
        return calendar.month_name[time.localtime().tm_mon]
    return calendar.month_name[int(x)]

def day(x):
    """Returns the name of a day from a day number or current day."""
    if not x:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[int(x)]

def year(x):
    """Returns the current year or the year from a timestamp."""
    if not x:
        return time.localtime().tm_year
    return time.localtime(int(x)).tm_year

def date(x, format='%Y-%m-%d'):
    """Returns the current date or the date from a timestamp."""
    if not x:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(x)))

def time(x, format='%H:%M:%S'):
    """Returns the current time or the time from a timestamp."""
    if not x:
        return time.strftime(format)
    return time.strftime(format, time.localtime(int(x)))

def zodiac(x):
    """Returns the zodiac sign for the current date or the date from a timestamp."""
    if not x:
        month = time.localtime().tm_mon
        day = time.localtime().tm_mday
    else:
        month = time.localtime(int(x)).tm_mon
        day = time.localtime(int(x)).tm_mday
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

def weekday(x):
    """Returns the weekday for the current date or the date from a timestamp."""
    if not x:
        return calendar.day_name[time.localtime().tm_wday]
    return calendar.day_name[time.localtime(int(x)).tm_wday]

def rand(x):
    """Returns a random number between 0 and 1."""
    if not x:
        return random.random()
    return random.random() * float(x)


def randint(x):
    """Returns a random integer between 0 and the input number."""
    return str(random.randint(0, int(x)))

def choice(x):
    """Returns a random item from a list."""
    return random.choice(x.split(','))

def shuffle(x):
    """Returns a shuffled list."""
    items = x.split(',')
    random.shuffle(items)
    return ','.join(items)

def sample(x, n='1'):
    """Returns n random items from a list."""
    items = x.split(',')
    random.shuffle(items)
    return ','.join(items[:int(n)])

def join(x, delimiter=','):
    """Joins a list into a string, separated by a delimiter."""
    return delimiter.join(x.split(','))

def sort(x):
    """Sorts a list."""
    items = x.split(',')
    items.sort()
    return ','.join(items)

def hide(x):
    """Hides a string by replacing it with asterisks."""
    return '*' * len(x)

def mask(x, n='4'):
    """Masks a string by replacing all but the last n characters with asterisks."""
    return '*' * (len(x) - int(n)) + x[-int(n):]

def truncate(x, n='50', ellipsis='...'):
    """Truncates a string to a specified length and adds an ellipsis."""
    return x[:int(n)] + ellipsis

def pad(x, n='50', character=' '):
    """Pads a string to a specified length with a specified character."""
    return x.ljust(int(n), character)

def scramble(x):
    """Scrambles the characters in a string."""
    items = list(x)
    random.shuffle(items)
    return ''.join(items)

def tag(x, tag='div', attributes=''):
    """Wraps a string in an HTML tag."""
    return f"<{tag} {attributes}>{x}</{tag}>"

def link(x, url):
    """Wraps a string in an HTML link."""
    return f'<a href="{url}">{x}</a>'

def image(x, url):
    """Wraps a string in an HTML image."""
    return f'<img src="{url}" alt="{x}">'

def style(x, style):
    """Wraps a string in an HTML style tag."""
    return f'<style>{style}</style>{x}'

def script(x, script):
    """Wraps a string in an HTML script tag."""
    return f'<script>{script}</script>{x}'

def html(x):
    """Escapes HTML characters."""
    return x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def json(x, index=None):
    """Converts a JSON string to a Python dictionary."""
    import json
    if not x:
        return json.loads(x)
    return json.loads(x)[index]

def toml(x, v=None):
    """Converts a TOML string to a Python dictionary."""
    try:
        import toml
    except ImportError:
        import tomllib as toml
    if not x:
        return toml.loads(x)
    return toml.loads(x)[index]

def yaml(x, index=None):
    """Converts a YAML string to a Python dictionary."""
    import yaml
    if not x:
        return yaml.safe_load(x)
    return yaml.safe_load(x)[index]

def markdown(x):
    """Converts a Markdown string to HTML."""
    import markdown
    return markdown.markdown(x)

def multiply(x, n):
    """Multiplies a string by a number."""
    # If x looks like a number do an actual multiplication
    if x.replace('.', '', 1).isdigit():
        return str(float(x) * float(n))
    return x * int(n)

def roman(x):
    """Converts an integer to a Roman numeral."""
    decimal = int(x)
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

def arabic(x):
    """Converts a Roman numeral to an integer."""
    roman = x.upper()
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

def binary(x):
    """Converts an integer to a binary string."""
    return bin(int(x))[2:]

def octal(x):
    """Converts an integer to an octal string."""
    return oct(int(x))[2:]

def hex(x):
    """Converts an integer to a hexadecimal string."""
    return hex(int(x))[2:]

def base64(x):
    """Converts a string to a base64 string."""
    import base64
    return base64.b64encode(x.encode()).decode()

def polybius(x):
    """Converts a string to a polybius cipher."""
    polybius_square = {
        'A': '11', 'B': '12', 'C': '13', 'D': '14', 'E': '15', 'F': '21', 'G': '22', 'H': '23', 'I': '24', 'J': '24', 'K': '25', 'L': '31', 'M': '32', 'N': '33', 'O': '34', 'P': '35', 'Q': '41', 'R': '42', 'S': '43', 'T': '44', 'U': '45', 'V': '51', 'W': '52', 'X': '53', 'Y': '54', 'Z': '55'
    }
    return ''.join([polybius_square.get(char.upper(), char) for char in x])

def rot13(x):
    """Converts a string to a rot13 cipher."""
    rot13_square = {
        'A': 'N', 'B': 'O', 'C': 'P', 'D': 'Q', 'E': 'R', 'F': 'S', 'G': 'T', 'H': 'U', 'I': 'V', 'J': 'W', 'K': 'X', 'L': 'Y', 'M': 'Z', 'N': 'A', 'O': 'B', 'P': 'C', 'Q': 'D', 'R': 'E', 'S': 'F', 'T': 'G', 'U': 'H', 'V': 'I', 'W': 'J', 'X': 'K', 'Y': 'L', 'Z': 'M'
    }
    return ''.join([rot13_square.get(char.upper(), char) for char in x])

def morse(x):
    """Converts a string to a morse code."""
    morse_square = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..'
    }
    return ' '.join([morse_square.get(char.upper(), char) for char in x])

def log(x):
    """Returns the natural logarithm of a number."""
    import math
    return math.log(float(x))

def log10(x):
    """Returns the base-10 logarithm of a number."""
    import math
    return math.log10(float(x))

def log2(x):
    """Returns the base-2 logarithm of a number."""
    import math
    return math.log2(float(x))

def sqrt(x):
    """Returns the square root of a number."""
    import math
    return math.sqrt(float(x))

def sin(x):
    """Returns the sine of a number."""
    import math
    return math.sin(float(x))

def cos(x):
    """Returns the cosine of a number."""
    import math
    return math.cos(float(x))

def tan(x):
    """Returns the tangent of a number."""
    import math
    return math.tan(float(x))

def asin(x):
    """Returns the arcsine of a number."""
    import math
    return math.asin(float(x))

def acos(x):
    """Returns the arccosine of a number."""
    import math
    return math.acos(float(x))

def atan(x):
    """Returns the arctangent of a number."""
    import math
    return math.atan(float(x))

def degrees(x):
    """Converts radians to degrees."""
    import math
    return math.degrees(float(x))

def radians(x):
    """Converts degrees to radians."""
    import math
    return math.radians(float(x))

def celcius(x):
    """Converts Fahrenheit to Celcius."""
    return (float(x) - 32) * 5 / 9

def fahrenheit(x):
    """Converts Celcius to Fahrenheit."""
    return float(x) * 9 / 5 + 32

def kelvin(x):
    """Converts Celcius to Kelvin."""
    return float(x) + 273.15

def imperial(x):
    """Converts metric units to imperial units."""
    return float(x) * 0.0393701

def metric(x):
    """Converts imperial units to metric units."""
    return float(x) * 25.4

def floor(x):
    """Rounds a number down to the nearest integer."""
    import math
    return math.floor(float(x))

def ceil(x):
    """Rounds a number up to the nearest integer."""
    import math
    return math.ceil(float(x))

def round(x):
    """Rounds a number to the nearest integer."""
    return int(float(x) + 0.5)

def abs(x):
    """Returns the absolute value of a number."""
    import math
    return math.fabs(float(x))

def factorial(x):
    """Returns the factorial of a number."""
    import math
    return math.factorial(int(x))

def isprime(x):
    """Returns True if a number is prime, False otherwise."""
    import math
    return math.isprime(int(x))

def add(x, n):
    """Adds a number to a number."""
    return float(x) + float(n)

def subtract(x, n):
    """Subtracts a number from a number."""
    return float(x) - float(n)

def divide(x, n):
    """Divides a number by a number."""
    return float(x) / float(n)

def negate(x):
    """Negates a number."""
    return -float(x)

def sign(x):
    """Returns the sign of a number."""
    return float(x) / abs(float(x))

def lunar(x):
    """Returns the current lunar phase or the lunar phase from a timestamp."""
    if not x:
        timestamp = time.time()
    else:
        timestamp = int(x)
    import ephem
    moon = ephem.Moon(timestamp)
    return str(moon.phase)

def search(x, substring):
    """Returns True if a substring is found in a string, False otherwise."""
    return substring in x

def length(x):
    """Returns the length of a string or list."""
    return len(x)

def lines(x):
    """Returns the number of lines in a string."""
    return len(x.split('\n'))

def words(x):
    """Returns the number of words in a string."""
    return len(x.split())

def average(x):
    """Returns the average of a list of numbers."""
    return sum([float(num) for num in x.split(',')]) / len(x.split(','))

def median(x):
    """Returns the median of a list of numbers."""
    items = [float(num) for num in x.split(',')]
    items.sort()
    if len(items) % 2 == 0:
        return str((items[len(items) // 2 - 1] + items[len(items) // 2]) / 2)
    return items[len(items) // 2]

def mode(x):
    """Returns the mode of a list of numbers."""
    items = [float(num) for num in x.split(',')]
    items.sort()
    max_count = 0
    max_item = None
    for item in items:
        count = items.count(item)
        if count > max_count:
            max_count = count
            max_item = item
    return max_item

def min(x):
    """Returns the minimum of a list of numbers."""
    items = [float(num) for num in x.split(',')]
    return min(items)

def max(x):
    """Returns the maximum of a list of numbers."""
    items = [float(num) for num in x.split(',')]
    return max(items)

def sum(x):
    """Returns the sum of a list of numbers."""
    items = [float(num) for num in x.split(',')]
    return sum(items)

def tarot(x):
    if not x:
        num = random.randint(0, 77)
    else:
        num = int(x)
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

def swapcase(x):
    """Swaps case of each character in the input string."""
    return x.swapcase()

def isnumeric(x):
    """Checks if the input string is numeric."""
    return x.isnumeric()

def isalpha(x):
    """Checks if the input string contains only alphabetic characters."""
    return x.isalpha()

def isalnum(x):
    """Checks if the input string contains only alphanumeric characters."""
    return x.isalnum()

def ord(x):
    """Converts a character to its Unicode code point."""
    return ord(x)

def chr(x):
    """Converts a Unicode code point to its corresponding character."""
    return int(x)

def urlencode(x):
    """URL-encodes the input string."""
    return urllib.parse.quote_plus(x)

def urldecode(x):
    """URL-decodes the input string."""
    return urllib.parse.unquote_plus(x)

def hash(x, method='sha256'):
    """Hashes the input string using the specified hash method."""
    if method == 'md5':
        return hashlib.md5(x.encode()).hexdigest()
    elif method == 'sha1':
        return hashlib.sha1(x.encode()).hexdigest()
    elif method == 'sha512':
        return hashlib.sha512(x.encode()).hexdigest()
    else:  # default to 'sha256'
        return hashlib.sha256(x.encode()).hexdigest()

def quote(x, quote_type="'"):
    """Adds quotes around a string."""
    return f"{quote_type}{x}{quote_type}"

def unquote(x):
    """Removes quotes around a string if present."""
    if (x.startswith("'") and x.endswith("'")) or (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    return x

def tetrad(x):
    """Converts a number input into the tetradic system."""
    T = ["D", "H", "C", "V"]
    if not x:
        return T
    return T[int(x) % 4]

def host(x):
    """Returns the local hostname or looks up the hostname of a host."""
    import socket
    if not x:
        try:
            local_hostname = socket.gethostname()
            return local_hostname
        except OSError as e:
            return f"Error getting local hostname: {e}"
    else:
        try:
            remote_hostname = socket.gethostbyname(x)
            return remote_hostname
        except socket.gaierror as e:
            return f"Error looking up host '{x}': {e}"

def cwd(x):
    """Returns the current dir or the closest matching sub-dir."""
    import os
    if not x:
        try:
            current_dir = os.getcwd()
            return current_dir
        except OSError as e:
            return f"Error getting current directory: {e}"
    else:
        try:
            current_dir = os.getcwd()
            items = os.listdir(current_dir)
            for item in items:
                item_path = os.path.join(current_dir, item)
                if os.path.isdir(item_path) and x in item:
                    return item_path
            return None # No matching directory found
        except OSError as e:
            return f"Error accessing directory: {e}"


# TODO: Allow builtins to be loaded from other locations
    

# Gather all the tools in one place
tools = {name: obj for name, obj in inspect.getmembers(sys.modules[__name__]) if inspect.isfunction(obj)}
tools["tools"] = tools
