# Parse a string from the command line.

import sys
from .sigils import Sigil


print(Sigil(sys.argv[1]))
