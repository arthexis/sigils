================
Sigils
================

Sigils is a Python library for powerful and flexible string interpolation.

Overview
========

Sigils extends Python's built-in string formatting capabilities with additional features like:

- Context-based interpolation: Sigils can be replaced by values from a context, which can be a dictionary or an object.
- Function execution: If a Sigil's value is a callable function, it can be executed and its return value used in the string.
- Nested and recursive interpolation: Sigils can be nested within other Sigils, and recursion is handled intelligently.
- Case-insensitive matching: If a key fails to resolve, a case-insensitive lookup is attempted.
- Global context: Alongside the context passed for each string, a global context can be maintained and used as a fallback.

Installation
============

Sigils can be installed via pip:

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

For more complex uses, such as function execution and nested interpolation, refer to the documentation and example code.

Use Cases
=========

Sigils can be used in a variety of scenarios:

- **Configuration File Generation**: Generate configuration files for various applications. The context could be loaded from a file or a database, and the output could be written to a config file.
- **Template Rendering**: Render templates for web pages, emails, or other forms of user-facing content. The context would typically be user data or other dynamic content.
- **Code Generation**: Generate code, for instance in a code-generation tool or a scaffolding tool.

Gotchas
=======

- **Execution of Functions**: If the value of a Sigil is a callable function, it will be executed and its return value used in the string. Ensure all function values in your context are safe to execute.
- **Recursion Depth**: By default, Sigils handles up to 6 levels of nested interpolation. Adjust this limit by passing a different `max_depth` value to the `interpolate` method.
- **Thread Safety**: The global context in Sigils is thread-safe. However, if you're using mutable objects in your context and you're modifying them from multiple threads, manage thread safety at the application level.
- **Case-Insensitive Matching**: If a key fails to resolve, a case-insensitive lookup is attempted. This only works if the keys in your context are all unique when lowercased.


Performance
===========

Sigils has been designed with performance in mind. While the exact performance can vary based on the complexity of your templates and the depth of your context objects, Sigils performs competitively with Python's built-in string formatting in many scenarios.

In a typical use case, with 10000 interpolations of a template with a medium-sized context, Sigils can complete the operation in around 0.02 seconds. For larger templates and contexts, the time increases, but remains within acceptable limits for most applications, including web applications.

Contributing
============

Contributions to Sigils are welcome! Please refer to the CONTRIBUTING.rst file for guidelines.

License
=======

Sigils is licensed under the MIT License. See the LICENSE file for details.
