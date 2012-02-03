# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source
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
##

from stoqlib.lib.algorithms import luhn
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Organisationsnummer
# http://sv.wikipedia.org/wiki/Organisationsnummer
# Skatteverket: SKV 709
#

class Organisationsnummer(object):
    label = 'Organisationsnr'
    entry_mask = '000000-0000'

    def validate(self, value):
        value = value.replace('-', '')
        if len(value) != 10:
            return False
        return luhn(value[:9]) == value[-1]

company_document = Organisationsnummer()


#
# Personnummer
# http://sv.wikipedia.org/wiki/Personnummer
# Skatteverket: SKV 707
#

class Personnummer(object):
    label = 'Personnummer'
    entry_mask = '000000-0000'

    def validate(self, value):
        value = value.replace('-', '')
        if len(value) != 10:
            return False
        return luhn(value[:9]) == value[-1]

person_document = Personnummer()


#
# Counties / Län
# http://en.wikipedia.org/wiki/Counties_of_Sweden
#

class County(object):
    label = 'Län'

    state_list = [
        "Blekinge",
        "Dalarna",
        "Gotland",
        "Gävleborg",
        "Halland",
        "Jämtland",
        "Jönköping",
        "Kalmar",
        "Kronoberg",
        "Norrbotten",
        "Skåne",
        "Stockholm",
        "Södermanland",
        "Uppsala",
        "Värmland",
        "Västerbotten",
        "Västernorrland",
        "Västmanland",
        "Västra Götaland",
        "Örebro",
        "Östergötland"]

    def validate(self, value):
        if value.lower() in [s.lower() for s in self.state_list]:
            return True
        return False

state = County()
