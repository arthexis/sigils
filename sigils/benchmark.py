import time
from sigils import Sigil

def run_benchmark(*, n=10000, debug=False):
    # Define a complex context
    complex_context = {
        "user": {
            "name": "Alice",
            "friends": [{"name": "Bob"}, {"name": "Charlie"}, {"name": "Dave"}],
            "greet": lambda name: f"Hello, {name}!"
        },
        "numbers": list(range(1000))
    }

    # Define the templates
    complex_template = """
        Hello, %[user.name]! You have %[user.friends.length] friends. 
        Your first friend is %[user.friends.0.name]. Number 500 is %[numbers.500].
        Your friends are: %[user.friends.0.name], %[user.friends.1.name], %[user.friends.2.name].
        Your last friend was %[user.friends.-1.name]. Second to last was %[user.friends.-2.name].

    """

    # Create Sigil instances
    complex_sigil = Sigil(complex_template)

    # Time the complex interpolation
    start = time.time()
    result = ""
    for _ in range(n):
        result = complex_sigil % complex_context
    end = time.time()
    print(f"Complex sigil interpolation took {end - start:.2f} seconds for {n} interpolations.")
    print(result)
