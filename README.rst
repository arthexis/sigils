Sigils
======

A **sigil** is a token embedded in text, used as a magical placeholder for abstract values. 
When resolved, the actual value can be extracted from a configurable thread-local context 
and replaced in the text or extracted from it.

This is different from conventional text formatting, in which you have to provide
the map of values in advance. The same sigil can be embedded in different contexts
(for example, an ORM query or an HTML template) and be resolved at runtime.

A sigil can also hold metadata, such as the type of the value, name of the field and model 
or remote resource where the data should be fetched from, conversion functions, etc. 
They can be useful for generating forms, URLs, SQL, etc. specially for rapid prototyping.

This library includes tools to extract, resolve, replace and define sigils.


.. _Documentation:


Installing
----------

Install and update using `pip`_:

.. code-block:: text

    pip install -U sigils


Structure of Sigils
-------------------

A typical sigil has one of the following forms in text:

.. code-block:: text

    [USERNAME]
    [SETTING.BASE_DIR]
    [MODEL='natural-key'.FIELD]
    [MODEL="natural-key".FIELD]
    [ENV=[TIER].HOST]
    [MODEL.USER=[USERNAME].STATUS]

Each sigil is a linked list of **nodes** separated by a dot.
Nodes can be **natural** or **parametrized**. 
Natural means, use the natural context to figure out the value. 
If parametrized, they can take an **argument** using the equals sign. 
The argument can be a number, a quoted string, or another sigil.

.. code-block:: text

    [NODE1='ARG1'.NODE2=[ARG2].NODE3=10.ETC]

Nesting can be done to any depth. If quotes are avoided around the inner sigils, 
data types will be preserved. If quotes are used, the result is always a string.


Whitespace
----------

Whitespace inside the sigil is ignored, so you can use it to make 
the sigils more readable. The following are all equivalent:

.. code-block:: text

    [MODEL='natural-key'.FIELD]
    [MODEL = 'natural-key' . FIELD]
    [MODEL='natural-key' .FIELD .SUBFIELD]

Whitespace inside quoted strings is preserved, so you can use it to
separate words in the argument:

.. code-block:: text

    [MODEL='natural key'.FIELD]
    [MODEL='natural-key'.FIELD]
    [MODEL='natural_key'.FIELD]

If you want to use quotes inside a quoted string, you can escape them:

.. code-block:: text

    [MODEL='natural "key"'.FIELD]
    [MODEL='natural \'key\''.FIELD]


Piping Values
-------------

The value can be piped into a function using the ``.`` operator. This
also allows piping the result of one sigil into another. For example:

.. code-block:: text

    [MODEL='natural-key'.FIELD.UPPER]
    [USER.NAME.UPPER.TRIM]
    [USER='arthexis@gmail.com'.DOMAIN.SLUGIFY]
    [USER=[USERNAME.TRIM].DOMAIN.SLUGIFY]


The function after ``.`` can be a built-in function, found in the current context, 
or a methon of the value. If the function is not found, the sigil is not resolved.
The function must accept one or two arguments. The first argument is the value
to be piped into the function. The second argument is the argument of the node
that contains the sigil. For example:


.. code-block:: text

    [MODEL='natural-key'.NAMES.FORMAT='Hello, {0}!']
    [SESSION.USER.ACCOUNT_ID.ZFILL=8]
    [DOM='#someid'.ELEM|STYLE='color: red;']


If the function fails, the sigil is not resolved.


Reserved Characters
-------------------

The following characters are reserved and cannot be used in sigils:

* ``[`` and ``]``: delimiters
* ``.``: node separator or function call
* ``'`` and ``"``: string delimiters
* ``=``: argument or natural key separator
* ``\``: escape character


Resolve and Replace
-------------------

The *resolve* function will replace any sigils found in a string with the
actual values from the context. It returns the resulting string.

.. code-block:: python

    from sigils import resolve, context

    with context(
        USERNAME="arthexis",
        SETTING={"BASE_DIR": "/home/arth/webapp"},
    ):
        result = resolve("[USERNAME]: [SETTINGS.BASE_DIR].")
        assert result == "arthexis: /home/arth/webapp"

All keys in the context mapping should be strings.
The use of uppercase keys is recommended but not required.
Values can be anything, a string, a number, a list, a dict,
or an instance of an ORM model.

.. code-block:: python

    class Model:
        owner = "arthexis"
                                       
    with context(
        MODEL: Model,                  # [MODEL.OWNER]
        UPPER: lambda x: x.upper(),    # [UPPER='text']
    ):
        assert resolve("[MODEL.OWNER.UPPER]") == "ARTHEXIS"

You can pass additional context to resolve directly: 

.. code-block:: python

    assert resolve("[NAME.UPPER]", context={"NAME": "arth"}) == "ARTH"


The *replace* function is similar to *resolve*, but it returns a tuple
with the result and a list of sigils that were not resolved:

.. code-block:: python

    from sigils import replace

    result, unresolved = replace("[MODEL.OWNER|UPPER]")
    assert result == "[MODEL.OWNER|UPPER]"
    assert unresolved == ["[MODEL.OWNER|UPPER]"]

    result, unresolved = replace("[MODCLS=1.OWNER|UPPER]", context={"MODCLS": Model})
    assert result == "ARTHEXIS"
    assert unresolved == []


The *replace* function doesn't resolve a sigil, instead it replaces it
with another pattern of text and extracts all sigils that were replaced.
This may also be useful for debugging and logging. For example:

.. code-block:: python

    from sigils import replace

    text, sigils = replace("select * from users where username = [USER]", "?")
    assert text == "select * from users where username = ?"
    assert sigils == ["[USER]"]


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

            sigils.set_context("MyModel", my_model_lookup)


You can change the callable param to make your model searchable with
a different argument or manager, here the primary key is used.

Then you can use something like this in your template:

.. code-block:: django

    {% load sigils %}
    {% sigil '[SOME_MODEL=[SESSION.USER].some_field]' %}

.. _simple tag: https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/#simple-tags


Project Dependencies
--------------------

.. _lark: https://github.com/lark-parser/lark
.. _pip: https://pip.pypa.io/en/stable/quickstart/


Features Roadmap
----------------

- [x] Update packaging to use pyproject.toml. 
- [X] Add 'sigil' project script to pyproject.toml.
- [ ] Improved built-in support for Django models.
- [X] Improved access to environment variables within SYS context.
- [ ] Support for custom gobal-level context functions (probably via a decorator).
- [ ] Support for list indexing and slicing.
- [ ] Ability to monkey-patch sigil functionality into existing classes.
- [ ] Ability to load context from a JSON, YAML, or TOML file.
- [ ] Consider additional OOTB operations: XPATH, REGEX, etc.
- [ ] Keep track of accessed context keys to optimize performance.
- [ ] API to resolve sigils remotely, cache results, browse context, etc.
- [ ] Benchmarking and performance improvements.
- [ ] More magic.


Protected Sigils (In Development)
---------------------------------

By starting a sigil with a ``.`` character, you can protect it from being
printed to logs unless the ``SIGILS_LOG_PROTECTED`` environment variable
is set to ``1``. This is useful for sensitive data such as passwords.

.. code-block:: text

    [.MODEL='natural-key'.PASSWORD]
    [.USER=[USERNAME].SECRET]


Instead of the sigil, its value will be replaced with ``[...]`` in the logs.
