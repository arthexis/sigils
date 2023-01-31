import sys
import logging
from .sigils import Sigil, local_context

def main():
    global DEBUG
    if len(sys.argv) < 2:
        print("Usage: sigils <string> [context=value]...")
        sys.exit(1)
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

    with local_context(**kwargs):
        logging.debug(f"Command-line context: {kwargs}")
        print(Sigil(sys.argv[1]))


__all__ = ["main"]
