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
from stoqlib.lib.cnab.febraban import (FileHeader, FebrabanCnab, BatchHeader,
                                       RecordP, RecordQ, RecordR)


class SantanderFileHeader(FileHeader):

    fields = FileHeader.fields[:]
    # Santander uses only 8 positions for the first cnab field
    fields[3] = Field('cnab', str, 8, '')

    replace_fields = {
        # And 15 positions instead of 14 for company document
        'company_document': [Field('company_document', int, 15)],
        'convenio': [
            Field('codigo_transmissao', int, 15),
            Field('_', str, 5)
        ],
        'agency': [Field('_', str, 5, '')],
        'agency_dv': [Field('_', str, 1, '')],
        'account': [Field('_', str, 12, '')],
        'account_dv': [Field('_', str, 1, '')],
        'dv_agencia_conta': [Field('_', str, 1, '')],
        'density': [Field('density', str, 5, '')],
    }


class SantanderBatchHeader(BatchHeader):
    replace_fields = {
        'convenio': [
            Field('_', str, 20, ''),
            Field('codigo_transmissao', int, 15),
            Field('_', str, 5, '')
        ],
        'agency': [],
        'agency_dv': [],
        'account': [],
        'account_dv': [],
        'dv_agencia_conta': [],
        'credit_date': [Field('_', str, 8, '')],
    }


class SantanderRecordP(RecordP):
    replace_fields = {
        'agency': [Field('agency', int, 4, '')],
        'agency_dv': [Field('_', int, 1, '')],
        'account': [Field('_', int, 9, '')],
        'account_dv': [Field('_', int, 1, '')],
        'dv_agencia_conta': [
            Field('conta_cobranca', int, 9, ''),
            Field('dv_conta_cobranca', int, 1, ''),
        ],
        'nosso_numero': [
            Field('_', str, 2, ''),
            Field('nosso_numero', int, 13),
        ],
        # Nota 5: 1 = Simples. Talvez precise ser customizavel pelo cliente.
        'tipo_carteira': [Field('tipo_cobranca', int, 1, 1)],
        # Nota 6: 1 = Registrada
        'tipo_cadastramento': [Field('tipo_cadastramento', int, 1, 1)],

        'emissao_boleto': [Field('_', str, 1, '')],
        'distribuicao': [Field('_', str, 1, '')],

        'charging_agency': [Field('charging_agency', int, 4, 0)],
        'charging_agency_dv': [
            Field('charging_agency_dv', int, 1, 0),
            Field('_', str, 1, ''),
        ],
        'contract_number': [Field('_', str, 10, '')],
    }


class SantanderRecordQ(RecordQ):
    fields = RecordQ.fields[:-1] + [
        Field('cnab', str, 19, ''),
    ]

    replace_fields = {
        # Ver nota 28
        'corresponding_bank': [Field('identificador_carne', int, 3, 0)],
        'corresponding_bank_nosso_numero': [
            Field('installment_number', int, 3, 0),
            Field('total_installments', int, 3, 0),
            Field('installment_plan', int, 3, 0),
        ]
    }


class SantanderRecordR(RecordR):
    # FIXME: This is only necessary if santander validates the unused fields.
    #fields = RecordQ.fields[:18] + [
    #    Field('cnab', str, 61, ''),
    #]

    replace_fields = {
        'discount3_code': [Field('_', str, 1, '')],
        'discount3_date': [Field('_', str, 8, '')],
        'discount3': [Field('_', str, 15, '')],
    }


class SantanderCnab(FebrabanCnab):
    FileHeader = SantanderFileHeader

    BatchHeader = SantanderBatchHeader

    RecordP = SantanderRecordP
    RecordQ = SantanderRecordQ
    RecordR = SantanderRecordR

    file_version = 40
    batch_version = 30
