# Parse a string from the command line.

import sys
from .sigils import Sigil, context
from .parsing import _try_call


import logging

# If --debug is in sys.argv, enable debug logging
# Remove --debug from sys.argv so it doesn't get passed to context

if DEBUG := "--debug" in sys.argv:
    sys.argv.remove("--debug")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(lineno)d %(message)s",
        handlers=[
            # logging.FileHandler("sigils.log"),
            logging.StreamHandler()
        ]
    )

if sys.argv[2:]:
    kwargs = dict(arg.split("=") for arg in sys.argv[2:] if "=" in arg)
    kwargs = {key.upper(): value for key, value in kwargs.items()}
    args = [arg for arg in sys.argv[2:] if "=" not in arg]
    if args:
        kwargs["ARGS"] = args
else:
    kwargs = {}

with context(**kwargs):
    logging.debug(f"Command-line context: {kwargs}")
    print(Sigil(sys.argv[1]))


