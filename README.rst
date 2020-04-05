Sigils
======

A **sigil** is a token embedded in text, used as a magical placeholder
for a future value. When resolved, the actual value can be extracted
from an user-provided thread-local context and replaced in the text
or extracted from it.

This library contains tools to extract, replace and resolve such sigils.


.. _Documentation:


Installing
----------

Install and update using `pip`_:

.. code-block:: text

    pip install -U sigils


Structure of Sigils
-------------------

A typical sigil has one of the following forms:

.. code-block:: text

    [USERNAME]
    [SETTING.BASE_DIR]
    [MODEL='natural-key'.FIELD]
    [MODEL="natural-key".FIELD]
    [ENV=[TIER].HOST]
    [MODEL.USER=[USERNAME].STATUS]

Each sigil is a list of **nodes** separated by a dot.
Nodes can be standalone or parametrized.
If parametrized, they can take an **argument** using the
equals sign. The argument can be a number, a quoted string,
or another sigil.

.. code-block:: text

    [NODE1='ARG1'.NODE2=[ARG2].NODE3=10.ETC]

Sigils used as arguments can be nested to any depth.


Resolving Sigils
----------------

The *resolve* function will replace any sigils found in a string,
given a context:

.. code-block:: python

    from sigils import resolve

    with context(
        USERNAME="arthexis",
        SETTING={"BASE_DIR": "/home/arth/webapp"},
    ):
        result = resolve("[USERNAME]: [SETTINGS.BASE_DIR].")
        assert result == "arthexis: /home/arth/webapp"

All keys in the context mapping should be strings.
Values can be anything, but usually it will be a string,
another dict, a callable or an instance with public fields:

.. code-block:: python

    class Model:
        owner = "arthexis"
                                         # Valid tokens
    context = {
        "USERNAME": "arthexis",          # [USERNAME]
        "SETTINGS": {"NAME": "webapp"},  # [SETTINGS.NAME]
        "MODEL": Model,                  # [MODEL.OWNER]
        "UPPER": lambda x: x.upper(),    # [UPPER='text']
        "RNG": lambda _: randint(),      # [RNG]
    }

Instead of passing the context explicitly,
a global default context can be set
to be used by all calls to *resolve*,
you can see an example in the Django integration below.



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

You can change the lambda to make your model searchable with
a different argument or manager, here the primary key is used.

Then you can use something like this in your template:

.. code-block:: django

    {% load sigils %}
    Some stuff: {% sigil '[MyModel=[obj.slug].some_field]' obj=foo %}

.. _simple tag: https://docs.djangoproject.com/en/2.2/howto/custom-template-tags/#simple-tags

Dependencies
------------

* lark_: Allows us to parse arbitrarily complex sigils fast.


.. _lark: https://github.com/lark-parser/lark
.. _pip: https://pip.pypa.io/en/stable/quickstart/
