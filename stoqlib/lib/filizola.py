# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import platform
import os

from stoqlib.lib.stringutils import strip_accents

from stoqlib.domain.sellable import Sellable


fields = [
    ('code', 6),
    ('weight_or_unity', 1),
    ('description', 22),
    ('price', 7),
    ('expire_days', 3),
    ('_', 126),
    ('tara', 4),
]

diversos = '1000000aDiversos              0000000000                                                                                                                             0000'  # nopep8


def generate_filizola_file(store):
    content = []
    content.append(diversos)

    for sellable in store.find(Sellable):
        try:
            # We can only send sellables whose code can be converted to integer
            code = int(sellable.code)
        except ValueError:
            continue

        if sellable.unit_description == 'Kg':
            unit = 'p'  # peso
        else:
            unit = 'u'  # unidade

        content.append("%06d%s%-22s%07d%03d%126s%04d" % (
            code,
            unit,
            str(strip_accents(sellable.description))[:22],
            int(sellable.price * 100),
            0,
            '',
            0,
        ))

    if platform.system() == 'Windows':
        dest_dir = os.path.join('C:\\', 'Filizola')
    else:
        # The software filizola provides is for windows, so on linux, it will
        # probably be running through wine (even though it didn't work properly
        # under wine).
        dest_dir = os.path.join('~', '.wine', 'drive_c', 'Filizola')
        dest_dir = os.path.expanduser(dest_dir)

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    dest = os.path.join(dest_dir, 'CADTXT.TXT')
    with open(dest, 'w') as fh:
        fh.write('\n'.join(content))

    return dest
