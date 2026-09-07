================
Sigils
================

"An inscribed or painted symbol considered to have magical power."

Sigils is a Python library for text and meta-text interpolation. It provides
context-based interpolation, function execution, nested and recursive
interpolation, ambient execution context, and a command-line interface.

Any Python object can be provided as explicit context, including nested
dictionaries, lists, and functions. Sigils can be used directly from Python or
from the command line. The core package has no required dependencies outside
of the Python standard library.

You may also install optional dependencies:

.. code-block:: bash

    pip install sigils[dotenv]
    pip install sigils[toml]
    pip install sigils[yaml]
    pip install sigils[markdown]
    pip install sigils[all]  # Installs everything


Installation
============

Install Sigils using pip:

.. code-block:: bash

    pip install sigils


Syntax
======

``[...]`` is the canonical sigil syntax. Normal sigils are lazy: wrapping text
in ``Sigil`` parses and preserves them, and they are resolved only when
``solve()`` or the ``%`` operator is used.

.. code-block:: python

    from sigils import Sigil

    template = Sigil("Hello, [user.name]!")
    context = {"user": {"name": "Alice"}}

    print(template.solve(context))  # Hello, Alice!
    print(template % context)       # Hello, Alice!

A leading ``%`` changes *when* a sigil is resolved. ``%[...]`` is eager and is
resolved as soon as the text is placed inside a ``Sigil`` envelope.

In Python, eager sigils use the current execution context in this order:

1. caller locals
2. caller globals
3. the active ``Context``
4. built-in Sigils tools

.. code-block:: python

    from sigils import Sigil

    name = "Alice"
    template = Sigil("Hello, %[name]!")

    print(template.template)  # Hello, Alice!

Normal and eager sigils can coexist. This allows early-bound values from the
execution environment and late-bound values supplied by a later caller:

.. code-block:: python

    from sigils import Sigil

    project = "gway"
    template = Sigil("Project: %[project], user: [user]")

    print(template.template)
    # Project: gway, user: [user]

    print(template.solve({"user": "Alice"}))
    # Project: gway, user: Alice

If an eager sigil cannot be resolved from the current execution context, it is
preserved intact so that a later explicit solve can still resolve it:

.. code-block:: python

    from sigils import Sigil

    template = Sigil("%[available_later]")
    print(template.template)  # %[available_later]

    print(template.solve({"available_later": "ready"}))
    # ready


Context
=======

``Context`` contributes ambient values to eager sigils without requiring those
values to be passed to every ``Sigil`` constructor.

.. code-block:: python

    from sigils import Context, Sigil

    with Context({"greeting": "Hello, world!"}):
        template = Sigil("%[greeting]")

    print(template.template)  # Hello, world!

Caller locals and globals take precedence over values from ``Context``.


Nested values, lists, and tools
===============================

Dotted sigils traverse nested dictionaries, lists, and object attributes:

.. code-block:: python

    from sigils import Sigil

    context = {
        "users": [
            {"name": "Alice"},
            {"name": "Bob"},
        ]
    }

    print(Sigil("[users.1.name]") % context)  # Bob

Built-in tools can be chained as part of an expression:

.. code-block:: python

    context = {"name": "alice"}

    print(Sigil("[name.upper]") % context)  # ALICE

Functions in the context may also be called. Arguments are separated from the
function name by spaces:

.. code-block:: python

    context = {
        "name": "Alice",
        "greet": lambda name: f"Hello, {name}!",
    }

    print(Sigil("[greet name]") % context)
    # Hello, Alice!

Prefixing an argument with ``%`` treats that argument as a literal value
instead of resolving it as another sigil:

.. code-block:: python

    print(Sigil("[greet %name]") % context)
    # Hello, name!


Recursive interpolation
=======================

Values may themselves contain sigils. Explicit resolution recursively resolves
lazy and eager sigils up to the configured maximum depth.

During constructor-time eager resolution, only eager sigils are consumed. If an
eager value expands to a lazy token, that lazy token remains available for a
later explicit solve.

.. code-block:: python

    from sigils import Sigil

    early = "[late]"
    template = Sigil("%[early]")

    print(template.template)  # [late]
    print(template.solve({"late": "resolved later"}))
    # resolved later


Command-Line Usage
==================

Sigils can be used directly from the command line. Context supplied to the CLI
resolves normal ``[...]`` sigils explicitly:

.. code-block:: bash

    sigils "Hello, [user.name]!" -c context.json

With a JSON context such as ``{"user": {"name": "Alice"}}``, the command
outputs ``Hello, Alice!``.


Considerations
==============

- **Function Execution**: If the value of a sigil is callable, it may be
  executed and its return value used in the string. Only provide contexts and
  tools that are safe to execute.
- **Recursion Depth**: Sigils resolves recursively up to 6 levels by default.
  Pass ``max_depth`` to ``Sigil`` to choose a different limit.
- **Thread Safety**: ``Context`` uses thread-local state. Mutable objects stored
  inside a context still require normal application-level synchronization.
- **Eager Python Context**: ``%[...]`` reads the Python caller's locals and
  globals. Use lazy ``[...]`` when a template should depend only on an explicit
  context supplied later.


Performance
===========

Sigils is designed with performance in mind. In typical use cases, Sigils
performs competitively with Python's built-in string formatting.


License
=======

See the repository LICENSE file for licensing terms.
