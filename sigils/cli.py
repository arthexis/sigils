import sys
import argparse
import os
import json
import tomllib as toml  # Use tomllib for Python 3.11+, fallback handled below

from .sigil import Sigil


def main():
    parser = argparse.ArgumentParser(description="Solve templates with %[sigils].")
    arg = parser.add_argument
    arg("text", nargs='?', default="", help="Text with %[sigils].")
    arg("--benchmark", "--bm", action='store_true', help="Run benchmark.")
    arg("--context", "--ctx", "--with", "-c", help="JSON/TOML/SQL/URL to gather context from.")
    arg("--debug", "-b", action='store_true', help="Print debug output.")
    arg("--expression", "--expr", "-e", help="Auto-wrap expression between %[brackets].")
    arg("--file", "--path", "--infile", "--source", "-f", "-s", help="Path to template file or directory.")
    arg("--list-sep", "--ls", default="|", help="Character(s) to use as list element separators.")
    arg("--max-depth", "-d", type=int, default=6, help="Maximum recursion depth allowed.")
    arg("--overwrite", "--replace", "--ow", "-r", action='store_true', help="Overwrite input file.")
    arg("--seed", type=int, default=None, help="Seed for random number generation.")
    arg("--make", nargs="?", default=None, help="Process .makefile template and run make with optional target.")
    arg("--test", action='store_true', help="Run test suite.")
    arg("--value", "-v", action='append', default=[], help='Additional context entries in KEY=VALUE format.')
    arg("--write", "--output", "--outfile", "--target", "-o", "-w", help="Write output to file.")
    arg("--release",  action="store_true", help="Build and upload the sigils package to PyPI.")
    
    args = parser.parse_args()
    Sigil.debug = args.debug
    
    if args.seed is not None:
        import random
        random.seed(args.seed)
    
    try:
        import loadenv
        loadenv.load()
    except ImportError:
        if args.debug:
            print("loadenv not installed. Skipping .env loading.")
    
    if args.test:
        import unittest
        suite = unittest.defaultTestLoader.discover('tests')
        unittest.TextTestRunner().run(suite)
    
    if args.benchmark:
        from .benchmark import run_benchmark
        run_benchmark(debug=args.debug)
    
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
        result = Sigil(text).solve(context=context, sep=args.list_sep)
        print(result)

    if args.make is not None:
        from .make import process_makefile, run_make
        makefile_path = process_makefile(os.getcwd(), context, args.debug)
        if makefile_path:
            run_make(os.getcwd(), args.make, args.debug)

    if args.release:
        from .release import update_patch_version, build_and_upload
        pyproject_path = "pyproject.toml"
        update_patch_version(pyproject_path, args.debug)
        build_and_upload(args.debug)


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
    result = sigil % context  # Same as sigil.solve(context)
    
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

                if debug:
                    print(f"Processing {input_path} -> {resolved_name}")

                if resolved_name == filename:
                    if debug:
                        print(f"Skipping {input_path}: filename did not resolve.")
                    continue

                output_path = os.path.join(root, resolved_name)
                process_file(input_path, output_path, context, debug)

                if debug:
                    print(f"Expected file created: {output_path}, Exists: {os.path.exists(output_path)}")

    
if __name__ == "__main__":
    main()
