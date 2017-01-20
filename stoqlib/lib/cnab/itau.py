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
from stoqlib.lib.cnab.febraban import (FileHeader, BatchHeader, RecordP,
                                       FebrabanCnab)


class ItauFileHeader(FileHeader):

    fields = FileHeader.fields[:-3] + [
        Field('_', str, 54, ''),
        Field('_', int, 3, 0),
        Field('_', str, 12, ''),
    ]


class ItauBatchHeader(BatchHeader):
    @property
    def credit_date(self):
        # Itau requires a credit_date.
        return self.get_value('create_date')


class ItauRecordP(RecordP):
    tipo_carteira = 0
    tipo_cadastramento = 0
    tipo_documento = '0'
    emissao_boleto = 0
    distribuicao = '0'
    interest_code = 0

    replace_fields = {
        'nosso_numero': [
            Field('carteira', int, 3),  # Nota 5
            Field('nosso_numero', int, 8),  # Nota 6
            Field('dac_nosso_numero', int, 1),  # Nota 25: dv do nosso numero
            Field('_', str, 8, ''),
        ],
        'numero_documento': [
            Field('numero_documento', str, 10),
            Field('_', str, 5, ''),
        ],
        'return_due_days': [Field('return_due_days', int, 2, 0)],
        'currency_code': [Field('_', int, 2, 0)],
        'contract_number': [Field('_', int, 11, 0)],
        'free_use': [Field('_', str, 1, '')],

    }


class ItauCnab(FebrabanCnab):
    FileHeader = ItauFileHeader
    BatchHeader = ItauBatchHeader
    RecordP = ItauRecordP

    file_version = 40
    batch_version = 30

    # Itau does not use this value (present in file header and batch header)
    convenio = ''

    # Even though the account may have a dv, it should not be in the cnab
    account_dv = ''

    # FIXME: Credit_date
