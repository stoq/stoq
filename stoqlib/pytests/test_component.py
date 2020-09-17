#
# Copyright (C) 2020 Stoq Tecnologia <http://www.stoq.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#

import pytest

from stoqlib.lib.component import (AlreadyImplementedError, Interface, _UtilityHandler, get_utility,
                                   provide_utility, remove_utility, implementer, utilities)

o = object()


@pytest.fixture(autouse=True, scope="function")
def patch_utilities(monkeypatch):
    monkeypatch.setattr('stoqlib.lib.component.utilities', _UtilityHandler())


class IBanana(Interface):
    pass


def test_utilities():
    assert isinstance(utilities, _UtilityHandler)


def test_get_utility():
    assert get_utility(IBanana, None) is None

    provide_utility(IBanana, o)
    with pytest.raises(TypeError):
        get_utility(object)

    assert get_utility(IBanana, o)


def test_provide_utility():
    with pytest.raises(NotImplementedError):
        get_utility(IBanana)

    provide_utility(IBanana, o)

    with pytest.raises(TypeError):
        provide_utility(object, o)


def test_remove_utility():
    with pytest.raises(TypeError):
        remove_utility(object)

    with pytest.raises(NotImplementedError):
        remove_utility(IBanana)

    provide_utility(IBanana, o)
    assert remove_utility(IBanana) == o

    with pytest.raises(NotImplementedError):
        remove_utility(IBanana)


def test_already_implmeneted_error():
    with pytest.raises(NotImplementedError):
        get_utility(IBanana)

    provide_utility(IBanana, o)

    with pytest.raises(AlreadyImplementedError):
        provide_utility(IBanana, o)


def test_zope_interface():
    try:
        from zope.interface import Interface
    except ImportError:
        return

    class IApple(Interface):
        pass

    with pytest.raises(NotImplementedError):
        get_utility(IApple)

    provide_utility(IApple, o)

    with pytest.raises(AlreadyImplementedError):
        provide_utility(IApple, o)


def test_implements():
    class I1(Interface):
        pass

    @implementer(I1)
    class C(object):
        pass

    c = C()
    x = object()
    assert I1.providedBy(x) is False
    assert I1.providedBy(c) is True


def test_interface_sub():
    class I1(Interface):
        pass

    class I2(I1):
        pass

    @implementer(I2)
    class C(object):
        pass

    @implementer(I1)
    class D(object):
        pass

    c = C()
    assert I1.providedBy(c) is True
    assert I2.providedBy(c) is True
    d = D()
    assert I1.providedBy(d) is True
    assert I2.providedBy(d) is False


def test_zope_implements():
    try:
        from zope.interface import Interface, implementer
    except ImportError:
        return

    class I1(Interface):
        pass

    @implementer(I1)
    class C(object):
        pass

    c = C()
    x = object()
    assert I1.providedBy(x) is False
    assert I1.providedBy(C) is False
    assert I1.providedBy(c) is True


def test_sope_interface_sub():
    try:
        from zope.interface import Interface, implementer
    except ImportError:
        return

    class I1(Interface):
        pass

    class I2(I1):
        pass

    @implementer(I2)
    class C(object):
        pass

    @implementer(I1)
    class D(object):
        pass

    c = C()
    assert I1.providedBy(c) is True
    assert I2.providedBy(c) is True
    d = D()
    assert I1.providedBy(d) is True
    assert I2.providedBy(d) is False
