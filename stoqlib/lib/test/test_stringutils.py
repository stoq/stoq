# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.lib.stringutils import next_value_for


def test_next_value_for():
    assert next_value_for(u"") == u"1"
    assert next_value_for(u"1") == u"2"
    assert next_value_for(u"999") == u"1000"
    assert next_value_for(u"A999") == u"A1000"
    assert next_value_for(u"A8") == u"A9"
    assert next_value_for(u"A9") == u"A10"
    assert next_value_for(u"A99") == u"A100"
    assert next_value_for(u"A999") == u"A1000"
    assert next_value_for(u"999A") == u"999A1"
    assert next_value_for(u"999A1") == u"999A2"
    #assert next_value_for(u"A999A") == u"A999B"
