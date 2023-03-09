import logging
import pathlib
import click    

from .tools import splice, execute
from .contexts import context as local_context

logging.basicConfig(level=logging.WARNING)


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
@click.option("--context", "-c", multiple=True,
        help="Context to use for resolving sigils."
            "Can be a file or a key=value pair. Multiple values are allowed.")
def main(text, on_error, verbose, default, interactive, file, exec, context):
    """Resolve sigils found in the given text."""
    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose > 1:
        logging.basicConfig(level=logging.DEBUG)

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
    print(f"Context: {context}")
    with local_context(*context):
        if not exec:
            result = splice(text, on_error=on_error, default=default)
        else:
            result = execute(text, on_error=on_error, default=default)
        print(result)

main()
