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

from decimal import Decimal

from stoqlib.lib.cnab.base import Field, Record, Cnab
from stoqlib.lib.formatters import format_address


class Record400(Record):
    size = 400


class ItauFileHeader(Record400):
    fields = [
        Field('registry_type', int, 1, 0),
        Field('operation_type', int, 1, 1),  # 1 = remessa
        Field('operation_name', str, 7, 'REMESSA'),
        Field('service_code', int, 2, 1),  # 01 == Cobrança
        Field('service_name', str, 15, 'COBRANCA'),
        Field('agency', int, 4),
        Field('_', int, 2, 0),
        Field('account', int, 5),
        Field('dv_agencia_conta', int, 1),
        Field('_', str, 8, ''),
        Field('company_name', str, 30),
        Field('bank_number', int, 3),
        Field('bank_name', str, 15),
        Field('create_date', int, 6),
        Field('_', str, 294, ''),
        Field('registry_sequence', int, 6),
    ]


class ItauPaymentDetail(Record400):
    fields = [
        Field('registry_type', int, 1, 1),
        Field('company_type', int, 2, 2),  # CPF/CNPJ 2 = CNPJ
        Field('company_document', int, 14),
        Field('agency', int, 4),
        Field('_', int, 2, 0),
        Field('account', int, 5),
        Field('dv_agencia_conta', int, 1),

        Field('_', str, 4, ''),
        # Instruçào a ser cancelada NOTA 27
        # Deve ser preenchido somente quando codigo_ocorrencia == 38
        Field('cancel_instruction', int, 4, 0),
        Field('payment_description', str, 25),
        Field('nosso_numero', int, 8),
        # Este campo deverá ser preenchido com zeros caso a moeda seja o Real.
        Field('variable_currency', Decimal, 8, 0, decimals=5),

        Field('carteira', int, 3),
        Field('bank_use', str, 21, ''),
        Field('codigo_carteira', str, 1),  # NOTA 5
        Field('codigo_ocorrencia', int, 2, 1),  # 01 == Remessa NOTA 6
        Field('numero_documento', str, 10),
        Field('due_date', int, 6),
        Field('value', Decimal, 11, decimals=2),

        Field('bank_number', int, 3),
        Field('charging_agency', int, 5, 0),
        Field('especie_titulo', str, 2, '01'),  # 01 - Duplicata Mercantil
        Field('aceite', str, 1),
        Field('open_date', int, 6),  # NOTA 31
        Field('instrucao_1', int, 2),  # NOTA 11
        Field('instrucao_2', int, 2),  # NOTA 11
        Field('interest_percentage', Decimal, 11),  # Juros de 1 dia

        Field('discount_date', int, 6, 0),
        Field('discount_value', Decimal, 11, 0),
        Field('iof', Decimal, 11, 0),
        Field('abatimento', Decimal, 11, 0),

        Field('payer_type', int, 2),  # CPF/CNPJ
        Field('payer_document', int, 14),
        Field('payer_name', str, 30),
        Field('_', str, 10, ''),
        Field('payer_address', str, 40),
        Field('payer_district', str, 12),
        Field('payer_postal_code', int, 8),
        Field('payer_city', str, 15),
        Field('payer_state', str, 2),
        Field('sacador_avalista', str, 30, ''),
        Field('_', str, 4, ''),
        Field('penalty_date', int, 6, 0),
        # Numero de dias para protestar/não receber/devolver/etc, dependendo do
        # valor das instrucoes 1 e 2
        Field('prazo', int, 2),  # NOTA 11 (A)
        Field('_', str, 1, ''),
        Field('registry_sequence', int, 6),
    ]

    # NOTA 5
    cod_carteira = {
        104: 'I',
        108: 'I',
        109: 'I',
        112: 'I',
        115: 'I',
        121: 'I',
        147: 'E',
        150: 'U',
        180: 'I',
        188: 'I',
        191: 'I',
    }

    def __init__(self, payment, bank_info, **kwargs):
        person = payment.group.payer
        if person.company:
            payer_type = 2
            doc = person.company.cnpj
        else:
            payer_type = 1
            doc = person.individual.cpf
        raw_doc = ''.join(i for i in doc if i.isdigit())

        address = person.get_main_address()
        postal_code = address.postal_code.replace('-', '')
        address_str = format_address(address, include_district=False)
        discount_value = bank_info.discount_percentage * payment.value
        kwargs.update(
            numero_documento=str(payment.identifier),
            due_date=payment.due_date.strftime('%d%m%y'),
            value=payment.value,
            payment_description=payment.description,
            open_date=payment.open_date.strftime('%d%m%y'),
            aceite=bank_info.aceite,
            nosso_numero=bank_info.nosso_numero,
            # Payer data
            payer_type=payer_type,
            payer_document=raw_doc,
            payer_name=person.name,
            payer_address=address_str,
            payer_district=address.district,
            payer_postal_code=postal_code.split('-')[0],
            payer_city=address.city_location.city,
            payer_state=address.city_location.state,
            # Desconto até o pagamento
            discount_date=payment.due_date.strftime('%d%m%y'),
            discount_value=discount_value,
        )
        super(ItauPaymentDetail, self).__init__(**kwargs)

    @property
    def codigo_carteira(self):
        carteira = self.get_value('carteira')
        return self.cod_carteira[int(carteira)]


class ItauPenaltyDetail(Record400):
    fields = [
        Field('registry_type', int, 1, 2),
        Field('penalty_code', str, 1, 2),  # 2 = valor percentual
        Field('penalty_date', int, 8),
        Field('penalty_percentage', Decimal, 11),
        Field('_', str, 371, ''),
        Field('registry_sequence', int, 6)
    ]

    def __init__(self, payment, bank_info, **kwargs):
        kwargs.update(
            penalty_date=payment.due_date.strftime('%d%m%Y'),
        )
        super(ItauPenaltyDetail, self).__init__(**kwargs)


class ItauFileTrailer(Record400):
    fields = [
        Field('registry_type', int, 1, 9),
        Field('_', str, 393, ''),
        Field('registry_sequence', int, 6),
    ]


class ItauCnab400(Cnab):

    def setup(self, payments):
        i = 1
        self.add_record(ItauFileHeader, registry_sequence=i)
        info_class = self.bank_info.__class__
        for payment in payments:
            info = info_class(payment)
            i += 1
            self.add_record(ItauPaymentDetail, payment, info, registry_sequence=i)
            if info.penalty_percentage > 0:
                i += 1
                self.add_record(ItauPenaltyDetail, payment, info, registry_sequence=i)

        self.add_record(ItauFileTrailer, registry_sequence=i + 1)

    @property
    def create_date(self):
        date = self.default_values['create_date']
        # the format here is ddmmaa, while the other is ddmmaaaa
        return date[:4] + date[-2:]
