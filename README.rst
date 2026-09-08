================
Sigils
================

"An inscribed or painted symbol considered to have magical power."

Sigils is a Python library for text and meta-text interpolation. It provides
context-based interpolation, function execution, nested and recursive
interpolation, ambient execution context, built-in transformation tools, and a
command-line interface.

The maintained PyPI distribution is named ``gway-sigils``. The Python package
and command-line interface remain named ``sigils``, so existing imports and
runtime usage are unchanged.

Any Python object can be provided as explicit context, including nested
dictionaries, lists, and functions. Sigils supports Python 3.11 and newer and
uses the standard-library ``tomllib`` module for TOML support.

Optional features can be installed individually or together:

.. code-block:: bash

    pip install gway-sigils[dotenv]
    pip install gway-sigils[yaml]
    pip install gway-sigils[markdown]
    pip install gway-sigils[astronomy]
    pip install gway-sigils[all]


Installation
============

Install Sigils using pip:

.. code-block:: bash

    pip install gway-sigils


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
preserved intact so that a later explicit solve can still resolve it.


Paths, calls, tuples, and fallbacks
===================================

Dots and whitespace both support traversal. Whitespace tries traversal first;
when traversal cannot continue through a normal callable, the historical
space-separated argument behavior remains available.

.. code-block:: text

    [health.errors]
    [health errors]
    [greet name]

The colon is the explicit call operator. Each colon-delimited segment after the
target is one argument. Whitespace around ``:``, ``,``, and ``=`` is ignored.
Arguments without ``=`` are positional; ``name=value`` is a keyword argument.
Multiple colons provide multiple arguments.

.. code-block:: text

    [network ip : wlan0]
    [network ip : interface=wlan0]
    [func : first : second]
    [func : left=first : right=second]
    [func : first : right=second]

``:=`` explicitly marks a positional argument. It is equivalent to an ordinary
positional segment, but is useful when the argument text itself contains an
``=`` and must not be interpreted as a keyword assignment.

.. code-block:: text

    [echo := value]
    [echo := left=right]

Commas do not create additional function arguments. Comma-separated members
inside one colon segment are resolved individually and passed as one tuple.
This also works for keyword arguments.

.. code-block:: text

    [func : a,b]
    [func : values=a,b,c]
    [func : first : options=a,b]

Prefixing a call value with ``%`` keeps that value literal rather than resolving
it from the context.

.. code-block:: text

    [greet : %name]

A final callable is invoked automatically, so ``[now]`` calls a zero-argument
``now`` value. A trailing colon with no right-hand side instead makes the left
side a literal constant: ``[now:]`` renders ``now``.

Fallback chains use ``|`` and ``||``. Loose ``|`` advances on any Python-falsey
value. Strict ``||`` advances only for an unresolved value, ``None``, or an
empty set/frozenset; values such as ``False``, ``0``, ``""``, ``[]``, ``{}``,
and ``()`` are retained. A branch beginning with ``:`` is a terminal literal
fallback.

.. code-block:: text

    [primary|backup|:offline]
    [primary||backup||:offline]


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

Functions in the context may also be called with the historical whitespace
syntax or the explicit colon syntax:

.. code-block:: python

    context = {
        "name": "Alice",
        "greet": lambda name: f"Hello, {name}!",
    }

    print(Sigil("[greet name]") % context)
    print(Sigil("[greet : name]") % context)
    # Hello, Alice!

Prefixing an argument with ``%`` treats that argument as a literal value
instead of resolving it as another sigil:

.. code-block:: python

    print(Sigil("[greet : %name]") % context)
    # Hello, name!

Multi-argument tools receive all declared arguments after each argument is
resolved. For example, structured-data tools can parse a value and select a
field in one expression:

.. code-block:: python

    context = {
        "payload": '{"name": "Alice"}',
        "field": "name",
    }

    print(Sigil("[json payload field]") % context)
    # Alice

The built-in ``sigil`` tool emits canonical lazy syntax, so applying it to
``name`` produces ``[name]`` rather than an eager token.


Protected namespaces
====================

``SafeNamespace`` prevents arbitrary attribute/tool fallthrough. A namespace
provider may explicitly return an approved callable by marking it with
``__sigils_safe_callable__ = True``. Sigils will invoke only such explicitly
approved callables when they originate inside a protected namespace. This lets
integrations expose a controlled command surface without exposing arbitrary
Python methods.


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
the supplied context. A resolved filename must remain a basename in the same
directory; absolute paths and parent-relative paths are rejected. Existing
destinations are also rejected unless ``--overwrite`` is explicitly supplied.
Symlinks are removed before an explicit overwrite so rendering never follows a
pre-existing symlink outside the selected directory.

``--value`` entries are merged only into mapping contexts. JSON list or scalar
contexts remain usable when no ``--value`` merge is requested.

The CLI deliberately contains only interpolation operations. Historical
benchmark, test-runner, make, and package-release switches are development
concerns and are no longer exposed as public CLI flags.


Protected values
================

``Secret`` marks a value as sensitive without changing sigil syntax. It is a
redaction and taint-propagation primitive, not encryption.

.. code-block:: python

    from sigils import Secret, Sigil

    password = Secret("swordfish")

    print(password)       # [REDACTED]
    print(repr(password)) # Secret('[REDACTED]')
    print(password.reveal())  # swordfish -- explicit trusted access

    template = Sigil("password=[password]")
    context = {"password": password}

    print(template.solve(context))
    # password=swordfish

    print(template.results(context))
    # {'password': '[REDACTED]'}

Template rendering is an intentional output operation, so it can consume the
real wrapped value. Resolver introspection through ``results()`` recursively
redacts protected values instead. Dotted traversal, built-in tools, callable
arguments, and recursive interpolation preserve the protection marker.

Eager protected values are captured out-of-band instead of storing their raw
text in the template:

.. code-block:: python

    password = Secret("swordfish")
    template = Sigil("password=%[password]")

    print(template.template)  # password=[REDACTED]
    print(template.solve())   # password=swordfish

Use ``reveal()`` only at an explicit trusted boundary. ``Secret`` does not stop
code that deliberately unwraps or renders the value; its purpose is to prevent
accidental disclosure through ordinary representations and introspection.


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
- **Environment Tool**: the ``env`` built-in exposes only explicitly allowlisted
  names. Common non-secret process values such as ``PATH``, ``HOME``, ``USER``,
  ``SHELL``, ``LANG``, ``PWD``, ``TERM``, and ``TZ`` are allowed by default.
  Embedding applications can expose additional names with the comma-separated
  ``SIGILS_ENV_ALLOWLIST`` environment variable. Unapproved names return an
  empty string, and requesting the complete environment returns only approved
  entries.
