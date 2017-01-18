# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2017 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.lib.cnab.base import Field
from stoqlib.lib.cnab.febraban import (RecordP,
                                       FebrabanCnab)


class BradescoRecordP(RecordP):

    replace_fields = {
        'nosso_numero': [
            Field('identificacao_produto', int, 3),  # Carteira?
            Field('_', int, 5, 0),
            Field('nosso_numero', int, 11),
            Field('dv_nosso_numero', int, 1),
        ],

    }


class BradescoCnab(FebrabanCnab):
    RecordP = BradescoRecordP

    file_version = 84
    batch_version = 42
