Sigils
======

*Inscribed or painted symbols considered to have magical power.*

A **sigil** is a universal token embedded in text, used as placeholder for out-of-context values. 
When resolved, the actual value is determined from a configurable thread-local context 
and interpolated into the text with proper formatting, extracted as a mapping, sanitized, etc.

This is different from conventional string interpolation, in which you have to provide
the map of values in advance. Instead, the same sigil can be embedded in different contexts
(SQL queries, HTML or email templates, configuration files, etc.) and be resolved only when needed.

A sigil can also hold metadata in it's filter structure, such as the type of value, the 
name of the field and model, or remote resource where the data should be fetched from, 
what functions should be applied to the found value, etc. 

Sigils includes all you need to manipulate text containing sigils.
It works with Django OOTB, but it can be used in any Python project.
Sigils is thread-safe and fast. It is also very easy to extend.

Sigils can be anywhere.


.. _Documentation:


Installation
------------

Install and update from PyPI:

.. code-block:: text

    pip install -U sigils


Structure of Sigils
-------------------

A typical sigil has one of the following forms in text:

.. code-block:: text

    [[USERNAME]]
    [[SETTING.BASE_DIR]]
    [[MODEL='natural-key'.FIELD]]
    [[MODEL="natural-key".FIELD]]
    [[ENV=TIER.HOST]]
    [[MODEL.USER=[USERNAME].STATUS]]

Each sigil is a linked list of **nodes** separated by a dot.
Nodes can be **natural** or **parametrized**. 
Natural means, use the natural context to figure out the value. 
If parametrized, they can take an **argument** using the equals sign. 

The argument can be a number, a quoted string, or another sigil.
When the argument is a sigil, only one brace pair is needed.

.. code-block:: text

    [[NODE1='ARG1'.NODE2=[ARG2].NODE3=10.ETC]]

Nesting can be done to any depth. If quotes are avoided around the inner sigils, 
data types will be preserved until the final interpolation.
If quotes are used, the result is always a string.


Whitespace
----------

Whitespace inside the sigil is ignored, so you can use it to make 
the sigils more readable. The following are all equivalent:

.. code-block:: text

    [[MODEL='natural-key' .FIELD]]
    [[MODEL  =  'natural-key'  .  FIELD]]
    [[ MODEL="natural-key" .FIELD.SUBFIELD ]]

Whitespace inside quoted strings is preserved, so you can use it to
separate words in the argument:

.. code-block:: text

    [[MODEL='natural key'.FIELD]]
    [[MODEL='natural-key'.FIELD]]
    [[MODEL='natural_key'.FIELD]]

If you want to use quotes inside a quoted string, you can escape them
or mix the quotes.

.. code-block:: text

    [[MODEL='natural "key"'.FIELD]]
    [[MODEL='natural \'key\''.FIELD]]


Piping Values and Functions
---------------------------

The found value can be piped into a function using the ``.`` operator. This
also allows piping the result of one sigil into another. For example:

.. code-block:: text

    [[MODEL='natural-key'.FIELD.UPPER]]
    [[USER.NAME.UPPER.TRIM]]
    [[USER='arthexis@gmail.com'.DOMAIN.SLUG]]
    [[USER=[USERNAME.TRIM].DOMAIN.SLUG]]


The function after ``.`` can be a built-in function, one found in the current context, 
or a method of the value (for example, if it was a model instance before being serialized for 
interpolation). If no function is found, the sigil is not resolved, even if a value was found.
The function must accept one or two arguments. The first argument is the value
to be piped into the function's first parameter. The second argument is the argument of 
the current node. For example:


.. code-block:: text

    [[MODEL='natural-key'.NAMES.FORMAT='Hello, {0}!']]
    [[SESSION.USER.ACCOUNT_ID.ZFILL=8]]
    [[DOM='#someid'.ELEM.STYLE='color']]


If the function fails, the sigil is not resolved. By default, no exceptions are raised
and not extraneous information is logged. 

Currently, the following built-in functions are available *everywhere*:

* ``SYS``: access system variables
* ``NUM``: convert to number
* ``UPPER``: convert to uppercase
* ``LOWER``: convert to lowercase
* ``TRIM``: remove leading and trailing whitespace
* ``STRIP``: idem
* ``SLUG``: convert to slug
* ``ZFILL``: zero-fill the string to the given length
* ``F``: format the found value using the given format string
* ``STYLE``: convert a CSS style string to a dict
* ``JOIN``: join the list with the given separator
* ``SPLIT``: split the string with the given separator
* ``OR``: return the found value, or the argument if None
* ``AND``: return the found value, or None if the argument is None
* ``NOT``: negate the found value
* ``BOOL``: convert to boolean
* ``INT``: convert to integer
* ``FLOAT``: convert to float
* ``LIST``: convert to list
* ``DICT``: convert to dict
* ``TUPLE``: convert to tuple
* ``SET``: convert to set
* ``JSON``: convert to JSON
* ``B64``: convert to base64
* ``B64D``: convert from base64
* ``URL``: convert to URL (percent-encoding)
* ``URLD``: convert from URL (percent-decoding)
* ``LEN``: return the length of the found value
* ``REV``: reverse the found value
* ``SORT``: sort the found value
* ``ITEM``: return an item of the found value explicitly by index or key
* ``KEY``: idem
* ``ATTR``: return an attribute of the found value explicitly by name
* ``ANY``: return True if any item in the found value is True
* ``ALL``: return True if all items in the found value are True
* ``NONE``: return True if all items in the found value are False
* ``SUM``: return the sum of the found value
* ``MIN``: return the minimum of the found value
* ``MAX``: return the maximum of the found value
* ``AVG``: return the average of the found value
* ``ABS``: return the absolute value of the found value
* ``ROUND``: return the rounded value of the found value
* ``CEIL``: return the ceiling value of the found value
* ``FLOOR``: return the floor value of the found value
* ``TRUNC``: return the truncated value of the found value
* ``MOD``: return the modulo of the found value
* ``FDIV``: return the floor division of the found value
* ``DIV``: return the division of the found value
* ``ADD``: return the sum of the found value and the argument
* ``SUB``: return the difference of the found value and the argument
* ``MUL``: return the product of the found value and the argument
* ``DIV``: return the quotient of the found value and the argument
* ``EQ``: return True if the found value is equal to the argument
* ``NE``: return True if the found value is not equal to the argument
* ``LT``: return True if the found value is less than the argument
* ``LE``: return True if the found value is less than or equal to the argument
* ``GT``: return True if the found value is greater than the argument
* ``GE``: return True if the found value is greater than or equal to the argument
* ``IN``: return True if the found value is in the argument
* ``CONTAINS``: idem but backwards
* ``FIRST``: return the first item of the found value
* ``LAST``: return the last item of the found value
* ``HEAD``: return the first N items of the found value
* ``TAIL``: return the last N items of the found value
* ``TYPE``: return the type of the found value	 
* ``FLAT``: flatten the found value
* ``UNIQ``: return the unique items of the found value
* ``ZIP``: zip the found value with the argument
* ``SIG``: treat the found value as a sigil (recursive interpolation)
* ``WORD``: return the Nth word of the found value

The SYS root function can be used to access system variables and special
functions. The sub-functions available may change depending on the context,
the current environment, user privileges and the installed packages. 

Currently these are available in all contexts:

* ``ENV``: access environment variables
* ``ARGS``: access all command-line arguments as a list
* ``OPTS``: idem
* ``NOW``: return the current datetime
* ``TODAY``: return the current date
* ``TIME``: return the current time
* ``UUID``: return a new UUID
* ``RNG``: return a random number
* ``PI``: return the value of pi
* ``PID``: return the current process ID
* ``PYTHON``: return the path to the python executable
* ``PY_VER``: return the version of the python interpreter
* ``SIG_VER``: return the version of the sigils package
* ``OS``: return the operating system name
* ``ARCH``: return the operating system architecture
* ``HOST``: return the hostname
* ``IP``: return the IP address
* ``USER``: return the username
* ``HOME``: return the home directory
* ``PWD``: return the current working directory
* ``CWD``: as above
* ``TMP``: return the path to the temporary directory


Special and Reserved Characters
-------------------------------

The following characters are reserved and cannot be used inside sigils, 
except as specified in this document:

* ``[[`` and ``]]``: delimiters
* ``.``: node separator or function call
* ``'`` and ``"``: string delimiters
* ``=``: argument or natural key separator
* ``\``: escape character
* ``(`` and ``)``: reserved for future use

Quotes can be used interchangeably, but they must be balanced.


Four Tools are Available
------------------------

The *spool* function iterates over all sigils in a string, yielding each one
in the same order they appear in the string, without resolving them.

.. code-block:: python

    from sigils import spool

    sql = "select * from users where username = [[USER]]"
    assert list(spool(sql)) == ["[[USER]]"]


Spoolling is a fast way to check if a string contains sigils without hitting the ORM
or the network. For example:

.. code-block:: python

    from sigils import spool

    if sigils := set(spool(text)):
        # do something with sigils
    else:
        # do something else


The *splice* function will replace any sigils found in the string with the
actual values from the context. Returns the interpolated string.

.. code-block:: python

    from sigils import splice, context

    with context(
        USERNAME="arthexis",
        SETTING={"BASE_DIR": "/home/arth/webapp"},
    ):
        result = splice("[[USERNAME]]: [[SETTINGS.BASE_DIR]].")
        assert result == "arthexis: /home/arth/webapp"

All keys in the context mapping should be strings (behavior is undefined if not)
The use of uppercase keys is STRONGLY recommended but not required.
Values can be anything, a string, a number, a list, a dict, or an ORM instance.

.. code-block:: python

    class Model:
        owner = "arthexis"
                                       
    with context(
        MODEL: Model,                  # [[MODEL.OWNER]]
        UPPER: lambda x: x.upper(),    # [[UPPER='text']]
    ):
        assert splice("[[MODEL.OWNER.UPPER]]") == "ARTHEXIS"

You can pass additional context to splice directly: 

.. code-block:: python

    assert splice("[[NAME.UPPER]]", context={"NAME": "arth"}) == "ARTH"

By default, the splice function will recurse into the found values,
interpolating any sigils found in them. This can be disabled by setting
the recursion parameter to 0. Default recursion is 6.

.. code-block:: python

    from sigils import splice, context

    with context(
        USERNAME="arthexis",
        DIR="/home/[[USERNAME]]",
        SETTING={"BASE_DIR": "[[DIR]]/webapp"},
    ):
        result = splice("[[USERNAME]]: [[SETTINGS.BASE_DIR]]", recursion=1)
        assert result == "arthexis: /home/[[USERNAME]]"


The function *resolve* is an alias for splice that never recurses.


The *execute* function is similar to resolve, but executes the found text 
as a python block (not an expression). This is useful for interpolating code:

.. code-block:: python

    from sigils import execute, context

    with context(
        USERNAME="arthexis",
        SETTING={"BASE_DIR": "/home/arth/webapp"},
    ):
        result = execute("print('[[USERNAME]]')")
        assert result == "arthexis"
        result = execute("print([[SETTING.BASE_DIR]])")
        assert result == "/home/arth/webapp"
        

Sigils will only be resolved within strings inside the code unless
the unsafe flag is set to True. For example:

.. code-block:: python

    from sigils import execute, context

    with context(
        USERNAME="'arthexis'",    
    ):
        result = execute("print([[USERNAME]])", unsafe=True)
        assert result == "arthexis"


The *vanish* function doesn't resolve sigils, instead it replaces them
with another pattern of text and extracts all the sigils that were replaced
to a map. This can be used for debugging, logging, async processing,
or to sanitize user input that might contain sigils.

.. code-block:: python

    from sigils import vanish

    text, sigils = vanish("select * from users where username = [[USER]]", "?")
    assert text == "select * from users where username = ?"
    assert sigils == ["[[USER]]"]


Async & Multiprocessing
-----------------------

All sigils are resolved asynchronously and in-parallel, so you can use 
them in loops, conditionals, and other control structures. For example:

.. code-block:: python

    from sigils import execute, context

    with context(
        USERNAME="arthexis",
        SETTING={"BASE_DIR": "/home/arth/webapp"},
    ):
        result = execute("if [[USERNAME]] == 'arthexis': print('yes')")
        assert result == "yes"


This can also make it more efficient to resolve documents with many sigils,
instead of resolving each one individually.


Django Integration
------------------

You can create a `simple tag`_ to resolve sigils in templates.
Create *<your_app>/templatetags/sigils.py* with the following code:

.. code-block:: python

    import sigils
    from django import templates

    register = template.Library()

    @register.simple_tag
    def resolve(text):
        return sigils.resolve(text)

In *app.py* add the following to register a model in the global context
(rename MyModel to the name of your model class):

.. code-block:: python

    import sigils
    from django.apps import AppConfig

    class MyAppConfig(AppConfig):
        def ready():
            from .models import MyModel

            def my_model_lookup(parent, slug):
                if not parent:
                    return MyModel.objects.filter(slug=slug)
                return parent.my_models.get(slug=slug)

            sigils.set_context("MY_MODEL", my_model_lookup)


You can change the callable param to make your model searchable with
a different argument or manager, here the primary key is used.

Then you can use something like this in your template:

.. code-block:: django

    {% load sigils %}
    {% sigil '[[SOME_MODEL=[USER].SOME_FIELD]]' %}

.. _simple tag: https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/#simple-tags


Command Line Interface
----------------------

The *sigils* command line tool can be used to resolve sigils in arguments
or files, with a given context. Example usage:

.. code-block:: bash

    $ sigils --help
    Usage: python -m sigils [OPTIONS] [TEXT]...

    Resolve sigils found in the given text.

    Options:
        -e, --on-error [raise|remove|default|ignore]
                                        What to do when a sigil cannot be resolved.
                                        Default: ignore.
        -d, --default TEXT              Default value for ignored sigils.
        -v, --verbose                   Increase verbosity.
        -i, --interactive               Enter interactive mode.
        -f, --file TEXT                 Read text from given file.
        -c, --context TEXT              Context to use for resolving sigils.
        --help                          Show this message and exit.

    $ sigils "Hello, [[USERNAME]]!" 
    # arthexis/sigils

    $ sigils -c "USERNAME=arthexis" README.md -o README2.md
    $ cat README2.md
    # arthexis/sigils


Project Dependencies
--------------------

* Python 3.9+
* `lark`_ for parsing
* `click`_ for the command line interface
* `pytest`_ for testing

.. _lark: https://github.com/lark-parser/lark
.. _pytest: https://docs.pytest.org/en/7.2.x/
.. _click: https://click.palletsprojects.com/en/7.x/


Feature Requests & Bug Reports
------------------------------

All feature requests and bug reports are welcome. Please open an issue on 
`GitHub Issues`_.

.. _GitHub Issues: https://github.com/arthexis/sigils/issues

Issues must use one of the approved templates. If you don't know which one
to use, use the "Bug Report" template. 


Special Thanks
--------------

My wife, Katia Larissa Jasso García, for the name "sigils".
