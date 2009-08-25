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
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##


import StringIO
from unicodedata import normalize
from xml.etree.ElementTree import tostring

import lxml.etree as ET

from stoqlib.database.runtime import get_connection

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

def get_uf_code_from_state_name(state_name):
    """Returns the UF code of a certain state. The UF code is Brazil specific.

    @param state_name: the state name in the short form (using two letters).
    @returns: a integer representing the uf code or None if we not find any
              uf code for the given state.
    """
    state = state_name.upper()
    if _uf_code.has_key(state):
        return _uf_code[state]

def get_city_code(city_name, state):
    """Returns the city code of a certain city. The city code is Brazil
    specific.
    @param city_name: the name of the city.
    @param state_name: the state name in the short form (using two letters).
    @returns: a integer representing the city code or None if we not find any
              city code for the given city.
    """
    uf_code = get_uf_code_from_state_name(state)
    city_name = remove_accentuation(city_name)
    city_data = NFeCityData.selectOneBy(city_name=city_name,
                                        uf_code=uf_code,
                                        connection=get_connection())
    if city_name is not None:
        return city_data.city_code

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
    message = tostring(element, 'utf8')
    node = ET.fromstring(message)
    tree = ET.ElementTree(node)
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
