================
Sigils
================

"An inscribed or painted symbol considered to have magical power."

Sigils is a Python library for text and meta-text interpolation. It provides advanced capabilities such as context-based interpolation, function execution, nested and recursive interpolation, case-insensitive matching, and global context support.

Any Python object can be provided as context, including nested dictionaries, lists, and functions. Sigils can be used directly from Python or from the command line. Sigils is thread-safe and has no required dependencies outside of the Python standard library.

You may also install optional dependencies:

.. code-block:: bash

    pip install sigils[dotenv]
    pip install sigils[toml]
    pip install sigils[all]  # Installs everything


Installation
============

Install Sigils using pip:

.. code-block:: bash

    pip install sigils

Usage
=====

Here's a simple example of using Sigils:

.. code-block:: python

    from sigils import Sigil

    context = {"user": {"name": "Alice"}}
    s = Sigil("Hello, %[user.name]!")
    print(s % context)  # Outputs: Hello, Alice!

Sigils can handle function execution and nested interpolation:

.. code-block:: python

    from sigils import Sigil

    context = {
        "user": {
            "name": "Alice",
            "greet": lambda name: f"Hello, {name}!"
        }
    }
    
    s = Sigil("%[user.greet:user.name]")
    print(s % context)  # Outputs: Hello, Alice!

    s = Sigil("%[user.greet:%%user.name]")
    print(s % context)  # Outputs: Hello, %user.name! %user.name is treated as a literal value

Sigils support case-insensitive matching and global context fallback:

.. code-block:: python

    from sigils import Sigil, Sigil.Context

    global_context = {"greeting": "Hello, world!"}
    with Sigil.Context(global_context):
        s = Sigil("%[GREETING]")
        print(s % {})  # Outputs: Hello, world!

Command-Line Usage
==================

Sigils can be used directly from the command line. Here's an example:

.. code-block:: bash

    sigils "Hello, %[user.name]!" -c context.json

In this example, "context.json" is a JSON file with a structure like {"user": {"name": "Alice"}}. The command will output: "Hello, Alice!".

Considerations
==============

- **Function Execution**: If the value of a Sigil is a callable function, it will be executed and its return value used in the string. Ensure all function values in your context are safe to execute.
- **Recursion Depth**: Sigils handles up to 6 levels of nested interpolation by default. Adjust this limit by passing a different `max_depth` value to the `interpolate` method.
- **Thread Safety**: The global context in Sigils is thread-safe. However, if you're using mutable objects in your context and modifying them from multiple threads, manage thread safety at the application level.
- **Case-Insensitive Matching**: If a key fails to resolve, a case-insensitive lookup is attempted. This only works if the keys in your context are all unique when lowercased.

Performance
===========

Sigils is designed with performance in mind. In typical use cases, Sigils performs competitively with Python's built-in string formatting.

License
=======

Sigils is licensed under the MIT License. See the LICENSE file for details.
