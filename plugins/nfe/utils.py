# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


import StringIO
from unicodedata import normalize
from xml.etree import ElementTree

from stoqlib.database.runtime import get_connection
from stoqlib.database.orm import AND, LIKE, ILIKE
from stoqlib.lib.parameters import sysparam

from nfedomain import NFeCityData

#
# Data
#

# UF code definition taken from IBGE

_uf_code = dict(# Norte
                RO=11,
                AC=12,
                AM=13,
                RR=14,
                PA=15,
                AP=16,
                TO=17,
                # Nordeste
                MA=21,
                PI=22,
                CE=23,
                RN=24,
                PB=25,
                PE=26,
                AL=27,
                SE=28,
                BA=29,
                # Sudeste
                MG=31,
                ES=32,
                RJ=33,
                SP=35,
                # Sul
                PR=41,
                SC=42,
                RS=43,
                # Centro-Oeste
                MS=50,
                MT=51,
                GO=52,
                DF=53)

#
# Functions
#


def get_state_code(state):
    """Returns the state code of a certain state (Brazil specific).

    @param state: the state name in the short form (using two letters).
    @returns: a integer representing the state code or None if we not find any
              code for the given state.
    """
    return _uf_code.get(state.upper())


def get_city_code(city_name, state=None, code=None):
    """Returns the city code of a certain city. The city code is Brazil
    specific.
    @param city_name: the name of the city.
    @param state: the state name in the short form (using two letters).
    @returns: a integer representing the city or None if the city was not
              found.
    """
    if code is None and state:
        state_code = get_state_code(state)
    else:
        state_code = code

    if state_code is None:
        conn = get_connection()
        # if the user informed an invalid state code, use a fallback value
        state_code = get_state_code(sysparam(conn).STATE_SUGGESTED)
    assert state_code is not None

    city_name = remove_accentuation(city_name)
    query = AND(NFeCityData.q.state_code == state_code,
                ILIKE(NFeCityData.q.city_name, city_name))
    city_data = NFeCityData.selectOne(query, connection=get_connection())
    if city_data is not None:
        return city_data.city_code


def get_cities_by_name(city, limit=20):
    """Returns a sequence of {NFeCityData} instances which the city name
    matches with the given city.
    """
    city_name = '%%%s%%' % remove_accentuation(city)
    results = NFeCityData.select(AND(LIKE(NFeCityData.q.city_name, city_name)),
                                  connection=get_connection())
    return results.limit(limit)


def remove_accentuation(string):
    """Remove the accentuantion of a string.
    @returns: the string without accentuantion.
    """
    # Taken from http://www.python.org.br/wiki/RemovedorDeAcentos
    return normalize('NFKD', string.decode('utf-8')).encode('ASCII', 'ignore')


def nfe_tostring(element):
    """Returns the canonical XML string of a certain element with line feeds
    and carriage return stripped.

    @param element: a xml.etree.Element instance.
    @returns: a XML string of the element.
    """
    message = ElementTree.tostring(element, 'utf8')
    node = ElementTree.XML(message)
    tree = ElementTree.ElementTree(node)
    # The transformation of the XML to its canonical form is required along
    # all the NF-e specification and its not supported by the xml.etree module
    # of the standard python library. See http://www.w3.org/TR/xml-c14n for
    # details.
    xml = StringIO.StringIO()
    tree.write_c14n(xml)

    xml_str = xml.getvalue()
    xml_str = xml_str.replace('\r', '')
    xml_str = xml_str.replace('\n', '')
    return xml_str
