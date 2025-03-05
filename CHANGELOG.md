Release Notes
=============

0.3.7 (2025-02-27)
-------------------

New in this version:

- The ARTHEXIS License
- Expression mode for CLI (-e)
- %[env.PATH] == %[PATH.env] (only True for env)
- Removed slow debug logging
- Replaced colon with spaces to call fuctions within sigils
- Allow solving %[sigils] for an entire directory recursively

In Progress:

- Proper configurable logging
- Rework Context to be more flexible


0.3.6 (2025-02-16)
-------------------

Completed:

- Fixed dependencies
- Added builting tool to gather other tools
- Improved benchmark
- Allow negative array on indexes (TODO: Test)
- Refactor sigil methods to leverage __init__

In Roadmap:

- Tests for loadenv
- Better docs for included functions
- Allow decimal numbers as keys


0.3.6 (2023-07-19)
-------------------

Add the --field command line option to the sigil command.

Refactor Sigil to split _resolve into "_resolve_map" and "_resolve_key".

0.3.5 (2023-07-17)
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
