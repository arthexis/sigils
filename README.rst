Sigils
======

A **sigil** is a token embedded in text, used as a placeholder
for a future value. When resolved, the actual value will be extracted
from an user-provided or global context.

This library contains tools to extract, replace and resolve such sigils.


.. _Documentation:


Installing
----------

Install and update using `pip`_:

.. code-block:: text

    pip install -U sigils


Using Sigils
------------

A typical sigil has one of the following forms:

.. code-block:: text

    [USERNAME]
    [SETTINGS.BASE_DIR]
    [MODEL='natural-key'.FIELD]
    [MODEL.USR=[USERNAME].STATUS]


Dependencies
------------

* lark_: Allows us to parse arbitrarily complex sigils fast.


.. _lark: https://github.com/lark-parser/lark
.. _pip: https://pip.pypa.io/en/stable/quickstart/
