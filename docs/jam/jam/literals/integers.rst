.. _jam-literals-integers:

Integers
########

A integer is a whole number of the builtin type ``Int``.

See the :ref:`builtin library <jam-builtins-numerical>` for more information
regarding the Integer type.

Syntax
======

.. productionlist::
    Integer: [0-9][ [0-9_]*[0-9] ]


Examples
--------

::

    # Mass of an object (kg)
    mass = 10

    # The speed of light (m/s)
    c = 299_792_458