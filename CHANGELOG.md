Release Notes
=============

0.3.5 (2023-07-16)
-------------------

Added (simplified) support for function tools once again.

This should work: %[sigil-name.field.upper]

0.3.4 (2023-07-16)
-------------------

Restore backwards compatibility with Python 3.9.

0.3.1 (2023-07-15)
-------------------

Complete revamp and simplification of the library.

Sigils now use the following syntax:

%[sigil-name]
%[sigil-name:arg1:arg2:...]
%[sigil_name]
%[sigil_name:key1=value1:key2=value2:...]

Check the new README.rst for more information.

0.2.9 (2023-03-27)
-------------------

- Refactored the FUNCTION_MAP into the *funcs.py* module.
- Added a simple benchmarking script.

0.2.7 (2023-03-14)
-------------------

- Fixed a bug in the *unvanish* function.

0.2.5 (2023-03-09)
-------------------

- Added pyyaml dependency.
- Added tox and githib actions for automated testing.

0.2.4 (2023-03-08)
-------------------

- Started keeping track of changes in this file.
- Fixed an error with the license.
- Added the *unvanish* function to the toolset.
- Renamed *local_context* to *context* (README.rst was right all along).
- New supported file types for context: .yaml, .toml, .ini, .json
