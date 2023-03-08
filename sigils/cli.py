import logging
import pathlib
import click    

from .sigils import splice, execute, local_context

logging.basicConfig(level=logging.WARNING)


# Function that recursively changes the keys of a dictionary
# to uppercase. This is used to convert the context dictionary
def _upper_keys(d):
    if isinstance(d, dict):
        return {k.upper(): _upper_keys(v) for k, v in d.items()}
    else:
        return d


@click.command()
@click.argument("text", nargs=-1)
@click.option("--on-error", "-e", 
        default="ignore", type=click.Choice(["raise", "remove", "default", "ignore"]), 
        help="What to do when a sigil cannot be resolved. Default: ignore")
@click.option("--default", "-d", default="", 
        help="Default value for ignored sigils.")
@click.option("--verbose", "-v", count=True, help="Increase verbosity.")
@click.option("--interactive", "-i", is_flag=True, help="Enter interactive mode.")
@click.option("--file", "-f", help="Read text from given file.")
@click.option("--exec", "-x", is_flag=True, help="Execute the text after resolving sigils.")
@click.option("--context", "-c", help="Context to use for resolving sigils.")
def main(text, on_error, verbose, default, interactive, file, exec, context):
    """Resolve sigils found in the given text."""
    _context = {}

    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

    if context:
        # If the context looks like a TOML file, load it
        if context.endswith(".toml"):
            import tomllib
            with open(context, 'r') as f:
                toml_data = tomllib.loads(f.read())
                _context.update(_upper_keys(toml_data))

    if interactive:
        import code
        def readfunc(prompt):
            line = input(prompt)
            line = splice(line, on_error=on_error, default=default)
            return line
        code.interact(local=locals(), readfunc=readfunc)
        return
    
    if file:
        # Convert path to absolute path
        file = pathlib.Path(file).resolve()
        with open(file, 'r') as f:
            text = f.read()
    else:
        text = " ".join(text)
    with local_context(**_context):
        if not exec:
            result = splice(text, on_error=on_error, default=default)
        else:
            result = execute(text, on_error=on_error, default=default)
        print(result)

main()
