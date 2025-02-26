import sys
import random
import argparse
from sigils import Sigil


def main():
    parser = argparse.ArgumentParser(description="Interpolate sigils in text.")
    parser.add_argument("text", nargs='?', default="", help="Text with sigils.")
    parser.add_argument("--file", "-f", help="Path to a file containing text with sigils.")
    parser.add_argument("--context", "-c", help="JSON/TOML file to provide context for interpolation.")
    parser.add_argument("--expression", "--expr", "-e", help="Wrap expression in %[sigils].")
    parser.add_argument("--index", "-i", help="A key used to narrow down the set of context values.")
    parser.add_argument("--max-depth", "-d", type=int, default=6, help="Maximum recursion depth.")
    parser.add_argument("--value", "-v", action='append', default=[], 
                        help='Additional context entries in the format KEY=VALUE. Can be used multiple times.')
    parser.add_argument("--test", action='store_true', help="Run tests.")
    parser.add_argument("--benchmark", action='store_true', help="Run benchmark.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for random number generation.")
    parser.add_argument("--dotenv", action='store_true', help="Load variables from a .env file.")
    parser.add_argument("--debug", action='store_true', help="Print debug output.")

    # TODO: Add --infile (-i) for loading a template from a given filename
    # TODO: Add --outfile (-o) for writing the output to a given filename 

    args = parser.parse_args()
    Sigil.debug = args.debug

    if args.seed is not None:
        random.seed(args.seed)
    if args.dotenv:
        from dotenv import load_dotenv
        load_dotenv()
    if args.test:
        import unittest
        from .tests import TestSigil
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSigil)
        unittest.TextTestRunner().run(suite)
    elif args.benchmark:
        from .benchmark import run_benchmark
        run_benchmark(debug=args.debug)
    else:
        # Load content from file if specified
        if args.file:
            with open(args.file, 'r') as file:
                template = file.read()
        else:
            template = args.text

        context_file = args.context
        if context_file:
            with open(context_file, 'r') as f:
                if context_file.endswith('.json'):
                    import json
                    context = json.load(f)
                elif context_file.endswith('.toml'):
                    try:
                        import tomllib as toml
                    except ImportError:
                        import toml
                    context = toml.load(f)
                else:
                    print(f"Unsupported file format: {context_file}", file=sys.stderr)
                    sys.exit(1)
        else:
            context = {}

        for entry in args.value:
            key, value = entry.split('=', 1)  # Split on the first '='
            context[key] = value
        if args.index:
            context = context.get(args.index)

        if args.expression:
            args.text = f"{args.text}%[{args.expression}]"
        sigil = Sigil(args.text)
        result = sigil.interpolate(context)
        print(result)

if __name__ == "__main__":
    main()
