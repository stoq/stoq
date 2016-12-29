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
from stoqlib.lib.cnab.febraban import (FileHeader, FileTrailer, BatchHeader,
                                       BatchTrailer, RecordQ, RecordP, RecordR,
                                       FebrabanCnab)


class CaixaFileHeader(FileHeader):
    convenio = '0' * 20

    replace_fields = {
        'account': [Field('codigo_beneficiario', int, 6)],
        'account_dv': [Field('_', int, 7, 0)],
    }


class CaixaBatchHeader(BatchHeader):

    replace_fields = {
        'convenio': [
            Field('codigo_beneficiario', int, 6),
            Field('_', int, 14, 0),
        ],
        'account': [Field('codigo_convenio', int, 6)],
        'account_dv': [Field('codigo_modelo_boleto', int, 7, 0)],
    }


class CaixaRecordP(RecordP):
    tipo_documento = 2  # = Escritural

    replace_fields = {
        'account': [Field('codigo_convenio', int, 6)],
        'account_dv': [Field('_', int, 7, 0)],
        'nosso_numero': [
            Field('_', int, 3, 0),
            # FIXME Ver nota G069 *
            Field('modalidade_carteira', int, 2, 0),
            Field('identificao_titulo', int, 15, 0),
        ],
        'numero_documento': [
            Field('numero_documento', str, 11),
            Field('_', str, 4, ''),
        ],
    }


class CaixaRecordQ(RecordQ):
    replace_fields = {
        # XXX: This is not respecting the documentation
        'corresponding_bank': [Field('corresponding_bank', str, 3, '')],
    }


class CaixaRecordR(RecordR):
    fields = RecordR.fields[:19] + [
        Field('payer_email', str, 50, ''),
        Field('cnab', str, 11, ''),
    ]


class CaixaBatchTrailer(BatchTrailer):

    replace_fields = {
        'cobranca_vinculada_qtd': [],
        'cobranca_vinculada_total': [],
        'aviso_lancamento': [Field('_', str, 31, '')],
    }


class CaixaFileTrailer(FileTrailer):
    replace_fields = {
        'total_concil': [Field('_', str, 6, '')],
    }


class CaixaCnab(FebrabanCnab):
    FileHeader = CaixaFileHeader
    FileTrailer = CaixaFileTrailer

    BatchHeader = CaixaBatchHeader
    BatchTrailer = CaixaBatchTrailer

    RecordP = CaixaRecordP
    RecordQ = CaixaRecordQ
    RecordR = CaixaRecordR

    file_version = 50
    batch_version = 30
