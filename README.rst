================
Sigils
================

"An inscribed or painted symbol considered to have magical power."

Sigils is a Python library for text and meta-text interpolation. It provides
context-based interpolation, function execution, nested and recursive
interpolation, ambient execution context, built-in transformation tools, and a
command-line interface.

Any Python object can be provided as explicit context, including nested
dictionaries, lists, and functions. Sigils supports Python 3.9 and newer.
Python 3.11+ uses the standard-library ``tomllib`` module; Python 3.9 and 3.10
automatically install ``tomli`` for equivalent TOML support.

Optional features can be installed individually or together:

.. code-block:: bash

    pip install sigils[dotenv]
    pip install sigils[yaml]
    pip install sigils[markdown]
    pip install sigils[astronomy]
    pip install sigils[all]


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
Explicit ``solve(context)`` resolution uses the context passed to ``solve``;
it does not implicitly merge the ambient ``Context``.


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

Dictionary keys are case-sensitive and exact. For example, ``[name]`` and
``[Name]`` may refer to two different values in the same context.

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

The built-in ``sigil`` tool emits canonical lazy syntax, so applying it to
``name`` produces ``[name]`` rather than an eager token.


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

The CLI resolves normal ``[...]`` sigils against values supplied on the command
line or loaded from a JSON/TOML context file:

.. code-block:: bash

    sigils "Hello, [user.name]!" -c context.json
    sigils "Hello, [name]!" -v name=Alice
    sigils -e name.upper -v name=alice

Use ``--max-depth`` to control recursive interpolation and ``--list-sep`` to
choose the separator used when a dictionary is rendered as its keys:

.. code-block:: bash

    sigils "[a]" -d 0 -v 'a=[b]' -v b=resolved
    sigils "[mapping]" -c context.json --list-sep ","

Files can be rendered to standard output, written elsewhere, or overwritten:

.. code-block:: bash

    sigils -f template.conf -c context.toml
    sigils -f template.conf -w generated.conf -c context.toml
    sigils -f template.conf -r -c context.toml

When ``-f`` points to a directory, files whose names contain sigils are
resolved recursively. Both the generated filename and its file contents use
the supplied context.

The CLI deliberately contains only interpolation operations. Historical
benchmark, test-runner, make, and package-release switches are development
concerns and are no longer exposed as public CLI flags.


Considerations
==============

- **Function Execution**: If the value of a sigil is callable, it may be
  executed and its return value used in the string. Only provide contexts and
  tools that are safe to execute.
- **Recursion Depth**: Sigils resolves recursively up to 6 levels by default.
  Pass ``max_depth`` to ``Sigil`` or ``--max-depth`` to the CLI to choose a
  different limit.
- **Thread Safety**: ``Context`` uses thread-local state. Mutable objects stored
  inside a context still require normal application-level synchronization.
- **Eager Python Context**: ``%[...]`` reads the Python caller's locals and
  globals. Use lazy ``[...]`` when a template should depend only on an explicit
  context supplied later.
- **Environment Tool**: the ``env`` built-in filters environment-variable names
  associated with credentials and secrets. Requesting the complete environment
  returns only non-sensitive entries.


Performance
===========

Sigils is designed with performance in mind. In typical use cases, Sigils
performs competitively with Python's built-in string formatting.


License
=======

Sigils is distributed under the ARTHEXIS License. See ``LICENSE`` for the full
terms.
