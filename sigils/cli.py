import argparse
import json
import os
import random

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import tomli as tomllib

from .sigil import Sigil


def build_parser():
    parser = argparse.ArgumentParser(description="Solve templates with [sigils].")
    arg = parser.add_argument
    arg("text", nargs="?", default="", help="Text containing [sigils].")
    arg("--context", "--ctx", "--with", "-c", help="JSON or TOML context file.")
    arg("--debug", "-b", action="store_true", help="Print debug output.")
    arg("--expression", "--expr", "-e", help="Auto-wrap an expression in [brackets].")
    arg("--file", "--path", "--infile", "--source", "-f", "-s", help="Template file or directory.")
    arg("--list-sep", "--ls", default="|", help="Separator used when rendering dictionary keys.")
    arg("--max-depth", "-d", type=int, default=6, help="Maximum recursive interpolation depth.")
    arg("--overwrite", "--replace", "--ow", "-r", action="store_true", help="Overwrite the input file.")
    arg("--seed", type=int, default=None, help="Seed the built-in random tools.")
    arg("--value", "-v", action="append", default=[], help="Additional context entry in KEY=VALUE form.")
    arg("--write", "--output", "--outfile", "--target", "-o", "-w", help="Write output to a file.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    Sigil.debug = args.debug

    if args.max_depth < 0:
        parser.error("--max-depth must be zero or greater")

    if args.seed is not None:
        random.seed(args.seed)

    try:
        import loadenv

        loadenv.load()
    except ImportError:
        if args.debug:
            print("loadenv not installed. Skipping .env loading.")

    try:
        context = load_context(args.context)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    for entry in args.value:
        if "=" not in entry:
            parser.error(f"invalid --value {entry!r}; expected KEY=VALUE")
        key, value = entry.split("=", 1)
        context[key] = value

    if args.file:
        if os.path.isdir(args.file):
            process_directory(
                args.file,
                context,
                args.debug,
                max_depth=args.max_depth,
                sep=args.list_sep,
            )
        else:
            output_path = args.file if args.overwrite else args.write
            process_file(
                args.file,
                output_path,
                context,
                args.debug,
                max_depth=args.max_depth,
                sep=args.list_sep,
            )
        return

    text = args.text
    if args.expression:
        text = f"{text}[{args.expression}]"
    result = Sigil(text, max_depth=args.max_depth).solve(
        context=context,
        sep=args.list_sep,
    )
    print(result)


def load_context(context_file):
    if not context_file:
        return {}

    extension = os.path.splitext(context_file)[1].lower()
    if extension == ".json":
        with open(context_file, "r", encoding="utf-8") as file:
            return json.load(file)

    if extension == ".toml":
        with open(context_file, "rb") as file:
            return tomllib.load(file)

    raise ValueError(
        f"unsupported context format {extension or '<none>'}; expected .json or .toml"
    )


def process_file(input_path, output_path, context, debug, *, max_depth=6, sep="|"):
    with open(input_path, "r", encoding="utf-8") as file:
        template = file.read()

    result = Sigil(template, max_depth=max_depth).solve(context, sep=sep)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(result)
        if debug:
            print(f"Written output to {output_path}")
    else:
        print(result)


def process_directory(directory, context, debug, *, max_depth=6, sep="|"):
    for root, _, files in os.walk(directory):
        for filename in files:
            if "[" not in filename or "]" not in filename:
                continue

            input_path = os.path.join(root, filename)
            resolved_name = Sigil(filename, max_depth=max_depth).solve(context, sep=sep)

            if debug:
                print(f"Processing {input_path} -> {resolved_name}")

            if resolved_name == filename:
                if debug:
                    print(f"Skipping {input_path}: filename did not resolve.")
                continue

            output_path = os.path.join(root, resolved_name)
            process_file(
                input_path,
                output_path,
                context,
                debug,
                max_depth=max_depth,
                sep=sep,
            )


if __name__ == "__main__":
    main()
