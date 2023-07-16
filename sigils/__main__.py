import argparse
import json
import tomllib as toml
import sys
import unittest
from collections import ChainMap
from sigils import Sigil

def flatten(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def main():
    parser = argparse.ArgumentParser(description="Interpolate sigils in text.")
    parser.add_argument("text", nargs='?', default="", help="Text with sigils.")
    parser.add_argument("--context", "-c", action='append', help="JSON/TOML file(s) to provide context for interpolation.")
    parser.add_argument("--execute", "-e", action='store_true', help="Execute callable values.")
    parser.add_argument("--max-depth", "-d", type=int, default=6, help="Maximum recursion depth.")
    parser.add_argument("--tests", action='store_true', help="Run tests.")
    args = parser.parse_args()

    if args.tests:
        from .tests import TestSigil
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSigil)
        unittest.TextTestRunner().run(suite)
    else:
        context_files = args.context if args.context else []
        contexts = []
        for context_file in context_files:
            with open(context_file, 'r') as f:
                if context_file.endswith('.json'):
                    context = flatten(json.load(f))
                elif context_file.endswith('.toml'):
                    context = flatten(toml.load(f))
                else:
                    print(f"Unsupported file format: {context_file}", file=sys.stderr)
                    sys.exit(1)
                contexts.append(context)

        chain_map = ChainMap(*reversed(contexts))  # Last context takes precedence
        print(Sigil(args.text) % chain_map)  

if __name__ == "__main__":
    main()
