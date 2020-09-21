import pytest

from stoqlib.lib.objutils import Settable, cmp, enum


class Status(enum):
    OPEN, CLOSE = range(2)


class Color(enum):
    RED, GREEN, BLUE = range(3)


def test_enum():
    assert issubclass(enum, int)
    assert isinstance(Color.RED, Color)
    assert isinstance(Color.GREEN, Color)
    assert isinstance(Color.BLUE, Color)
    assert 'RED' in repr(Color.RED)
    assert int(Color.RED) == 0


def test_enum_get():
    assert Color.get(0) == Color.RED

    with pytest.raises(TypeError):
        Color.get('RED')

    with pytest.raises(ValueError):
        Color.get(-10)


def test_enum_repeated_value():
    with pytest.raises(ValueError):
        class Repeated(enum):
            FOO = 0
            BAR = 0


def test_settable():
    obj = Settable(foo=1, bar=2)
    assert obj.foo == 1
    assert obj.bar == 2

    obj.foo = 10
    obj.bar = 20
    obj.baz = 30

    assert obj.foo == 10
    assert obj.bar == 20
    assert obj.baz == 30


def test_settable_getattributes():
    obj = Settable(foo=1, bar=2)

    assert obj.getattributes() == obj._attrs


def test_cmp():
    assert cmp(1, 1) == 0
    assert cmp(1, 20) == -1
    assert cmp(20, 1) == 1
    assert cmp([1, 2, 3], [3, 4, 5]) == -1
    assert cmp([1, 2, 3], [1, 2, 3]) == 0
    assert cmp([3, 4, 5], [1, 2, 3]) == 1
