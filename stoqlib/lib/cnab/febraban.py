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
"""Default febraban CNAB specification

This is implementing the default febraban specification for CNAB files. Ususally
banks have replaced some fields with different ones, or don't even use some of
the fields available, or have different default values for the fields.
"""

from decimal import Decimal

from stoqlib.lib.cnab.base import Record, Field, Cnab
from stoqlib.lib.formatters import format_address


REGISTER_FILE_HEADER = 0
REGISTER_BATCH_HEADER = 1
REGISTER_BATCH_INITIAL = 2
REGISTER_DETAIL = 3
REGISTER_BATCH_FINAL = 4
REGISTER_BATCH_TRAILER = 5
REGISTER_FILE_TRAILER = 9

DOCUMENT_TYPE_CPF = 1
DOCUMENT_TYPE_CNPJ = 2
DOCUMENT_TYPE_PIS = 3

CNAB_TYPE_REMESSA = 1
CNAB_TYPE_RETURN = 2

SERVICE_CODE_COBRANCA = 1

# Movement type constants
# See field description C004
MOVEMENT_TYPE_REGISTER = 1
MOVEMENT_TYPE_REMOVE = 2
MOVEMENT_TYPE_CHANGE_DUE_DATE = 3
MOVEMENT_TYPE_ADD_DISCOUNT = 4
MOVEMENT_TYPE_CANCEL_DISCOUNT = 5
# and so on ...

# Wallet type constants
# See field description C006
WALLET_SIMPLE_CHARGING = 1
WALLET_VINCULATED_CHARGING = 2
WALLET_SECURED_CHARGING = 3
WALLET_DISCOUTED_CHARGING = 4
WALLET_VENDOR = 5

# See field description C007
WALLET_REGISTERED = 1
WALLET_NOT_REGISTERED = 2


class FileHeader(Record):
    fields = [
        # Control
        Field('bank_number', int, 3),
        Field('batch', int, 4, 0),
        Field('registry_type', int, 1, REGISTER_FILE_HEADER),

        Field('cnab', str, 9, ''),

        # Company data
        Field('company_type', int, 1, DOCUMENT_TYPE_CNPJ),
        Field('company_document', int, 14),
        Field('convenio', str, 20),
        Field('agency', int, 5),
        Field('agency_dv', str, 1),
        Field('account', int, 12),
        Field('account_dv', str, 1),
        Field('dv_agencia_conta', int, 1),
        Field('company_name', str, 30),

        Field('bank_name', str, 30),
        Field('cnab', str, 10, ''),

        # File data
        Field('code', int, 1, CNAB_TYPE_REMESSA),
        Field('create_date', int, 8),
        Field('create_time', int, 6),
        Field('sequence', int, 6, 1),
        Field('file_version', int, 3),
        Field('density', int, 5, 0),

        Field('cnab', str, 20, ''),
        Field('company_reserved', int, 20, ''),
        Field('cnab', str, 29, ''),
    ]


class BatchHeader(Record):
    """Header do lote de cobrança (seção 3.2.2 da documentação Febraban)
    """

    fields = [
        # Control
        Field('bank_number', int, 3),
        Field('batch', int, 4, 1),
        Field('registry_type', int, 1, REGISTER_BATCH_HEADER),

        # Service
        Field('operation', str, 1, 'R'),  # G028
        Field('service_code', int, 2, SERVICE_CODE_COBRANCA),  # G025
        Field('cnab', int, 2, 0),
        Field('batch_version', int, 3),

        Field('cnab', str, 1, ''),

        # Company
        Field('company_type', int, 1, DOCUMENT_TYPE_CNPJ),
        Field('company_document', int, 15),

        #: Company contract number with the bank
        Field('convenio', str, 20),
        Field('agency', int, 5),
        Field('agency_dv', str, 1),
        Field('account', int, 12),
        Field('account_dv', str, 1),
        Field('dv_agencia_conta', int, 1),  # G012
        Field('company_name', str, 30),

        #: Messages for when the bank is printing the bill
        Field('message1', str, 40, ''),
        Field('message2', str, 40, ''),

        Field('batch_sequence', int, 8, 0),  # para uso da empresa - G079
        Field('save_date', int, 8, 0),  # G068

        #: Date that the value was credited in the bank account. Present only in
        #: return file
        Field('credit_date', int, 8, 0),  # C003
        Field('cnab', str, 33, ''),
    ]


class RecordP(Record):
    """Bill information

    This record is mandatory

    This includes the due date, value, interests
        movement_code: 01 / 02 / etc...
    """
    fields = [
        # Control data 1 - 3
        Field('bank_number', int, 3),
        Field('batch', int, 4, 1),  # Mesmo que o numero do lote
        Field('registry_type', int, 1, REGISTER_DETAIL),

        # Service 4 - 7
        Field('registry_sequence', int, 5),  # Numero sequencial
        Field('segment', str, 1, 'P'),
        Field('cnab', str, 1, ''),
        Field('movement_code', int, 2, MOVEMENT_TYPE_REGISTER),  # C004

        # account data 8 - 12
        Field('agency', int, 5),
        Field('agency_dv', str, 1),
        Field('account', int, 12),
        Field('account_dv', str, 1),
        Field('dv_agencia_conta', int, 1),

        # Nosso numero - 13
        Field('nosso_numero', str, 20),

        # Charging details - 14 - 18
        Field('tipo_carteira', int, 1, WALLET_SIMPLE_CHARGING),  # C006
        Field('tipo_cadastramento', int, 1, WALLET_REGISTERED),  # C007
        Field('tipo_documento', str, 1, ''),  # C008

        #: Who is reponsible to emit the bill
        Field('emissao_boleto', int, 1, 2),  # 2 = cliente emite

        #: Who is responsible to distribute the bill
        Field('distribuicao', str, 1, '2'),  # 2 = cliente distribui


        # 19 - 26 Bill data
        #: Numero do documento de cobraça. Pode ser o identificador da venda ou
        #: do pagamento. Diferente do nosso numero, dependendo do banco.
        Field('numero_documento', str, 15),  # C011
        Field('due_date', str, 8),
        Field('value', Decimal, 13),

        Field('charging_agency', int, 5, 0),
        Field('charging_agency_dv', int, 1, 0),
        Field('especie_titulo', int, 2, 2),  # 02 - duplicata mercantil
        Field('aceite', str, 1),  # A / N
        Field('open_date', int, 8),

        # 27 - 29 - Interest
        Field('interest_code', int, 1, 1),  # 1 = valor por dia
        Field('interest_date', int, 8, 0),  # 0 = data vencimento
        Field('interest_value', Decimal, 13),  # valor monetário / dia

        # 30 - 32 - Discount
        Field('discount_code', int, 1, 2),  # 2 = Percentual até data informada
        Field('discount_date', int, 8),
        Field('discount_percentage', Decimal, 13),

        Field('iof', Decimal, 13, 0),
        Field('abatimento', Decimal, 13, 0),
        Field('company_identifier', str, 25, ''),  # Para uso da empresa
        Field('protest_code', int, 1, 3),  # 3 - Não protestar
        Field('days_to_protest', int, 2, 0),
        Field('return_code', int, 1, 0),  # Não tratado
        Field('return_due_days', int, 3, 0),  # Não tratado
        Field('currency_code', int, 2, 9),
        Field('contract_number', int, 10, 0),  # Não tratado
        Field('free_use', str, 1, ''),
    ]

    def __init__(self, payment, bank_info, **kwargs):
        # valor monetário do juros diário. Como não tem opção de informar o
        # juros diário em percetual (somente mensal), precisamos infromar o
        # valor fixo.
        interest = bank_info.interest_percentage * payment.value

        kwargs.update(
            numero_documento=str(payment.identifier),
            due_date=payment.due_date.strftime('%d%m%Y'),
            value=payment.value,
            open_date=payment.open_date.strftime('%d%m%Y'),
            aceite=bank_info.aceite,
            nosso_numero=bank_info.nosso_numero,
            # Desconto até o vencimento
            discount_date=payment.due_date.strftime('%d%m%Y'),
            interest_value=interest
        )
        super(RecordP, self).__init__(**kwargs)


class RecordQ(Record):
    """Information about the payer

    This record is mandatory
    """
    fields = [
        # 1 - 3 Control data
        Field('bank_number', int, 3),
        Field('batch', int, 4, 1),  # Mesmo que o numero do lote
        Field('registry_type', int, 1, REGISTER_DETAIL),

        # 4 - 7 Service
        Field('registry_sequence', int, 5),  # Numero sequencial
        Field('segment', str, 1, 'Q'),
        Field('cnab', str, 1, ''),
        Field('movement_code', int, 2, 1),  # Same as Record P

        # 8 - 16 - Payer info
        Field('payer_type', str, 1),
        Field('payer_document', int, 15),
        Field('payer_name', str, 40),
        Field('payer_address', str, 40),
        Field('payer_district', str, 15),
        Field('payer_postal_code', int, 5),
        Field('payer_postal_code_complement', int, 3),
        Field('payer_city', str, 15),
        Field('payer_state', str, 2),

        # 17 - 19 - Sacador/avalista
        Field('sacador_type', int, 1, 0),
        Field('sacador_doc', int, 15, 0),
        Field('sacador_name', str, 40, ''),

        Field('corresponding_bank', int, 3, 0),
        Field('corresponding_bank_nosso_numero', str, 20, ''),
        Field('cnab', str, 8, ''),
    ]

    def __init__(self, payment, bank_info, **kwargs):
        person = payment.group.payer
        if person.company:
            payer_type = 2
            doc = person.company.cnpj
        else:
            payer_type = 1
            doc = person.individual.cpf
        raw_doc = ''.join(i for i in doc if i in '1234567890')
        address = person.get_main_address()

        postal_code = address.postal_code or '-'
        address_str = format_address(address, include_district=False)
        kwargs.update(
            payer_type=payer_type,
            payer_document=raw_doc,
            payer_name=person.name,
            payer_address=address_str,
            payer_district=address.district,
            payer_postal_code=postal_code.split('-')[0],
            payer_postal_code_complement=postal_code.split('-')[1],
            payer_city=address.city_location.city,
            payer_state=address.city_location.state,
        )
        super(RecordQ, self).__init__(**kwargs)


class RecordR(Record):
    """Additional discount/surchage/messages
    """
    fields = [
        # 1 - 3 Control data
        Field('bank_number', int, 3),
        Field('batch', int, 4, 1),  # Mesmo que o numero do lote
        Field('registry_type', int, 1, REGISTER_DETAIL),

        # 4 - 7 Service
        Field('registry_sequence', int, 5),  # Numero sequencial
        Field('segment', str, 1, 'R'),
        Field('cnab', str, 1, ''),
        Field('movement_code', int, 2, 1),  # Same as Record P

        # 8 - 10 - Disconut 2 - Não tratados
        Field('discount2_code', int, 1, 0),
        Field('discount2_date', int, 8, 0),
        Field('discount2', Decimal, 13, 0),

        # 11 - 13 - Discount 3 - Não tratados
        Field('discount3_code', int, 1, 0),
        Field('discount3_date', int, 8, 0),
        Field('discount3', Decimal, 13, 0),

        # 14 - 16 - Penalty
        Field('penalty_code', int, 1, 2),  # 2 = Percentual
        Field('penalty_date', int, 8, 0),  # 0 = data vencimento
        Field('penalty_percentage', Decimal, 13),

        Field('message_to_payer', str, 10, ''),
        Field('message3', str, 40, ''),
        Field('message4', str, 40, ''),
        Field('cnab', str, 20, ''),
        Field('payer_occur_code', int, 8, 0),

        # - 22 - 27
        Field('debit_bank', int, 3, 0),
        Field('debit_agency', int, 5, 0),
        Field('debit_agency_dv', str, 1, ''),
        Field('debit_account', int, 12, 0),
        Field('debit_account_dv', str, 1, ''),
        Field('debit_account_ag_dv', str, 1, ''),
        Field('debit_warn', int, 1, 0),
        Field('cnab', str, 9, ''),
    ]

    def __init__(self, payment, bank_info, **kwargs):
        super(RecordR, self).__init__(**kwargs)


class BatchTrailer(Record):
    fields = [
        # Control
        Field('bank_number', int, 3),
        Field('batch', int, 4, 1),
        Field('registry_type', int, 1, REGISTER_BATCH_TRAILER),

        Field('cnab', str, 9, ''),

        # File data - G057
        Field('total_registries', int, 6),

        # Descrições C070 and C071
        # This totalizers are only present in the return file.
        Field('cobranca_simples_qtd', int, 6, 0),
        Field('cobranca_simples_total', Decimal, 15, 0),
        Field('cobranca_vinculada_qtd', int, 6, 0),
        Field('cobranca_vinculada_total', Decimal, 15, 0),
        Field('cobranca_caucionada_qtd', int, 6, 0),
        Field('cobranca_caucionada_total', Decimal, 15, 0),
        Field('cobranca_descontada_qtd', int, 6, 0),
        Field('cobranca_descontada_total', Decimal, 15, 0),

        # C072
        Field('aviso_lancamento', int, 8, 0),
        Field('cnab', str, 117, ''),
    ]

    @property
    def total_registries(self):
        # 2 = FileHeader + BatchTrailer + FileTrailer
        return len(self.cnab.records) - 3

    @property
    def cobranca_simples_qtd(self):
        # 4 = FileHeader + BatchHeader + BatchTrailer + FileTrailer
        # 3 = number of details / payment
        return (len(self.cnab.records) - 4) / 3


class FileTrailer(Record):
    fields = [
        # Control
        Field('bank_number', int, 3),
        Field('batch', int, 4, 9999),
        Field('registry_type', int, 1, REGISTER_FILE_TRAILER),

        Field('cnab', str, 9, ''),

        # Totals
        Field('total_batches', int, 6, 1),
        Field('total_records', int, 6),
        Field('total_concil', int, 6, 0),

        Field('cnab', str, 205, ''),
    ]


class FebrabanCnab(Cnab):
    FileHeader = FileHeader
    FileTrailer = FileTrailer

    BatchHeader = BatchHeader
    BatchTrailer = BatchTrailer

    RecordP = RecordP
    RecordQ = RecordQ
    RecordR = RecordR

    #: Version of the file record. Subclasses must define this if they are
    #: using the default febraban FileHeader record
    file_version = None

    #: Version of the batch record. Subclasses must define this if they are
    #: using the default febraban BatchHeader record
    batch_version = None

    def setup(self, payments):
        self.add_record(self.FileHeader)
        self.add_record(self.BatchHeader)
        info_class = self.bank_info.__class__
        for i, payment in enumerate(payments):
            info = info_class(payment)
            self.add_record(self.RecordP, payment, info, registry_sequence=3 * i + 1)
            self.add_record(self.RecordQ, payment, info, registry_sequence=3 * i + 2)
            self.add_record(self.RecordR, payment, info, registry_sequence=3 * i + 3)

        self.add_record(self.BatchTrailer)
        self.add_record(self.FileTrailer)

    @property
    def total_records(self):
        return len(self.records)
