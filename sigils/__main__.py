import sys
import random
import argparse
import os
import json
import tomllib as toml  
from sigils import Sigil


def load_context(context_file):
    if not context_file:
        return {}
    
    with open(context_file, 'r') as f:
        if context_file.endswith('.json'):
            return json.load(f)
        elif context_file.endswith('.toml'):
            try:
                return toml.load(f)
            except ImportError:
                import toml  # Fallback for older Python versions
                return toml.load(f)
        else:
            print(f"Unsupported format: {context_file}", file=sys.stderr)
            sys.exit(1)


def process_file(input_path, output_path, context, debug):
    with open(input_path, 'r') as file:
        template = file.read()
    
    sigil = Sigil(template)
    result = sigil % context
    
    if output_path:
        with open(output_path, 'w') as file:
            file.write(result)
        if debug:
            print(f"Written output to {output_path}")
    else:
        print(result)


def process_directory(directory, context, debug):
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.startswith('%[') and filename.endswith(']'):
                input_path = os.path.join(root, filename)
                resolved_name = Sigil(filename).solve(context)
                if resolved_name == filename:
                    if debug:
                        print(f"Skipping {input_path}: filename did not resolve.")
                    continue
                output_path = os.path.join(root, resolved_name)
                process_file(input_path, output_path, context, debug)


def main():
    parser = argparse.ArgumentParser(description="Solve templates with %[sigils].")
    parser.add_argument("text", nargs='?', default="", help="Text with %[sigils].")
    parser.add_argument("--file", "--path", "--infile", "--source", "-f", "-s", help="Path to a file or directory.")
    parser.add_argument("--context", "--with", "-c", help="JSON/TOML file to provide context.")
    parser.add_argument("--expression", "--expr", "-e", help="Wrap expression in %[sigils].")
    parser.add_argument("--max-depth", "-d", type=int, default=6, help="Maximum recursion depth.")
    parser.add_argument("--value", "-v", action='append', default=[], help='Additional context entries in KEY=VALUE format.')
    parser.add_argument("--test", action='store_true', help="Run test suite.")
    parser.add_argument("--benchmark", action='store_true', help="Run benchmark.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for random number generation.")
    parser.add_argument("--write", "--output", "--outfile", "--target", "-w", help="Write output to file.")
    parser.add_argument("--overwrite", "--replace", "-o", "-r", action='store_true', help="Overwrite input file.")
    parser.add_argument("--debug", "-b", action='store_true', help="Print debug output.")
    
    args = parser.parse_args()
    Sigil.debug = args.debug
    
    if args.seed is not None:
        random.seed(args.seed)
    
    try:
        import loadenv
        loadenv.load()
    except ImportError:
        if args.debug:
            print("loadenv not installed. Skipping .env loading.")
    
    if args.test:
        import unittest
        from .tests import TestSigil
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSigil)
        unittest.TextTestRunner().run(suite)
        return
    
    if args.benchmark:
        from .benchmark import run_benchmark
        run_benchmark(debug=args.debug)
        return
    
    context = load_context(args.context)
    for entry in args.value:
        key, value = entry.split('=', 1)
        context[key] = value
    
    if args.file:
        if os.path.isdir(args.file):
            process_directory(args.file, context, args.debug)
        else:
            output_path = args.file if args.overwrite else args.write
            process_file(args.file, output_path, context, args.debug)
    else:
        text = args.text if not args.expression else f"{args.text}%[{args.expression}]"
        result = Sigil(text, debug=debug) % context
        print(result)
    
    
if __name__ == "__main__":
    main()
