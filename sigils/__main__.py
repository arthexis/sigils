import argparse
import sys
from sigils import Sigil

def main():
    parser = argparse.ArgumentParser(description="Interpolate sigils in text.")
    parser.add_argument("text", nargs='?', default="", help="Text with sigils.")
    parser.add_argument("--context", "-c", help="JSON/TOML file to provide context for interpolation.")
    parser.add_argument("--target", "-t", help="Target key in the context for interpolation.")
    parser.add_argument("--execute", "-e", action='store_true', help="Execute callable values.")
    parser.add_argument("--max-depth", "-d", type=int, default=6, help="Maximum recursion depth.")
    parser.add_argument("--test", action='store_true', help="Run tests.")
    args = parser.parse_args()

    if args.test:
        import unittest
        from .tests import TestSigil
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSigil)
        unittest.TextTestRunner().run(suite)
    else:
        context_file = args.context
        if context_file:
            with open(context_file, 'r') as f:
                if context_file.endswith('.json'):
                    import json
                    context = json.load(f)
                elif context_file.endswith('.toml'):
                    import tomllib as toml
                    context = toml.load(f)
                else:
                    print(f"Unsupported file format: {context_file}", file=sys.stderr)
                    sys.exit(1)
        else:
            context = {}

        if args.target:
            context = context.get(args.target)

        print(Sigil(args.text).interpolate(context)) 

if __name__ == "__main__":
    main()
