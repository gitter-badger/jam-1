.. _jam-builtins-numerical:

Builtin Numerical Types
#######################

Jam provides both a set of generic numerical classes which abstract away the
underlying implementation, as well as common numerical types bound to their
underlying implementation.

Generic Numerical Classes
=========================

.. code-block:: Jam

    class Int
    class UInt

\

    A generic integer class, either signed or unsigned able to represent
    virtually infinitely large numbers (limited only by memory) and the default
    type for any integer literal.

    Note that being unrestricted has a performance impact on the class. For
    performance critical code the use of sized integer types is suggested.

    .. code-block:: Jam

        self + other:Int
        self - other:Int
        self * other:Int
        self // other:Int
        self ** other:Int

    \

        All standard mathematical operations except normal division are
        supported by this class.

    .. code-block:: Jam

        self:Real

    \

        Ints may be implicitly cast to real numbers, resulting in normal
        divisions of integers returning reals.

    .. code-block:: Jam

        self as Int8
        self as Int16
        self as Int32
        self as Int64
        self as Int128

    \

        Ints may be explicitly cast to any sized integer type, possibly
        resulting in an exception if the size of the integer is larger than the
        requested type.

    .. code-block:: Jam

        self as Byte[]

    \

        The underlying representation can be obtained by explicitly casting to a
        Byte array.

    .. code-block:: Jam

        self as UInt

    \

        The `Int` class may be explicitly cast to `UInt`. If the number is
        negative an exception is thrown.

    .. code-block:: Jam

        self:Int

    \

        The `UInt` class may be implicitly cast to `Int`.

.. code-block:: Jam

    class Real
    class UReal

\

    A generic real number class is an arbitrary precision floating point number
    and the default type for any real number literal.

    .. code-block:: Jam

        self + other:Real
        self - other:Real
        self * other:Real
        self / other:Real
        self ** other:Real

    \

        All standard mathematical operations except integer division are
        supported by this class.

    .. code-block:: Jam

        self as Float32
        self as Float64

    \

        Any real may be cast to any sized floating point type, possibly
        resulting in an exception if the sizes are incompatible.

    .. code-block:: Jam

        self as Int

    \

        Any real may also be explicitly cast to an integer. The resulting
        integer is guaranteed to be rounded to the correct integer number.

    .. code-block:: Jam

        self as Byte[]

    \

        The underlying representation can be obtained by explicitly casting to a
        Byte array.

Sized Numeric Classes
=====================

.. code-block:: Jam

    class Int8
    class Int16
    class Int32
    class Int64
    class Int128
    class UInt8
    class UInt16
    class UInt32
    class UInt64
    class UInt128

\

    Each `IntXXX` and `UIntXXX` class is a direct mapping to integers (signed
    or unsigned) of `XXX` number of bits. Operations with these types are
    typically single instructions and thereby faster than their generic
    counterparts.

    .. code-block:: Jam

        self + other:T
        self - other:T
        self * other:T
        self // other:T
        self ** other:T

    \

        All operations except for normal division are supported.

    .. code-block:: Jam

        self:Int

    \

        Any `IntXXX` or `UIntXXX` may be implicitly cast to `Int`

    .. code-block:: Jam

        self:UInt

    \

        Any `UIntXXX` may be implicitly cast to `UInt`

    .. code-block:: Jam

        self as IntXXX
        self as UIntXXX

    \

        Any `T` may be explicitly cast to any other sized integer type.

    .. code-block:: Jam

        self as Byte[]

    \

        Any `IntXXX` or `UIntXXX` may be cast to it's underlying representation.

.. code-block:: Jam

    class Float32
    class Float64
    class UFloat32
    class UFloat64

\

    Each `FloatXX` and `UFloatXX` class is a direct mapping to floating point
    numbers (signed or unsigned) of `XX` number of bits. Operations with these
    types are typically single instructions and thereby a lot faster than their
    generic counterparts.

    .. code-block:: Jam

        self + other:T
        self - other:T
        self * other:T
        self / other:T
        self ** other:T

    \

        All operations except for integer division are supported.

    .. code-block:: Jam

        self:Real

    \

        Any `FloatXX` or `UFloatXX` may be implicitly cast to `Real`.

    .. code-block:: Jam

        self:UReal

    \

        Any `UFloatXX` may be implicitly cast to `UReal`

    .. code-block:: Jam

        self as FloatXX
        self as UFloatXX

    \

        Any `T` may be explicitly cast to any other sized integer type.

    .. code-block:: Jam

        self as Byte[]

    \

        Any `FloatXX` or `UFloatXX` may be cast to it's underlying
        representation.
