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


#
# Data
#

# UF code definition taken from IBGE

_uf_code = dict(# Norte
                RN=11,
                AC=12,
                AM=13,
                RR=14,
                PA=15,
                AP=16,
                TO=17,
                # Nordeste
                MA=21,
                PI=22,
                CE=24,
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
    state = state_name.upper()
    if _uf_code.has_key(state):
        return _uf_code(state)
