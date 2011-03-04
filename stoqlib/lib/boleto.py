# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011 Async Open Source
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
"""Boleto generation code.

For now, configuration will be stored inside stoq.conf. As a workaround, I
added IStoqConfig, so that stoqlib can get the stoq config. Remove this once
we have the financial app.

A sample configuration follows:

[Boleto]
; Boleto section should inform the bank code, and can provide up to 3 lines
; to add at the instructions field.

; There should be another section named after the bank_id, that stores the
; information abount the account destination of the bill
banco = 001

instrucao1 = Primeia linha da instrução
instrucao2 = Segunda linha da instrução
instrucao3 = Terceira linha da instrução

[104]
; Nossa Caixa
carteira = 18
agencia = 1565
conta = 414

[001]
; Banco do Brasil
convenio = 12345678
len_convenio = 8
agencia = 1172
conta = 403005

"""

import datetime
import tempfile

from kiwi.datatypes import Decimal
from kiwi.component import get_utility

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.message import warning

from pyboleto.data import get_bank
from pyboleto.pdf import BoletoPDF

_ = stoqlib_gettext

def can_generate_bill():
    config = get_utility(IStoqConfig)
    has_bank = config.has_option('banco', section='Boleto')
    has_section = False
    if has_bank:
        has_section = config.has_section(config.get_option('banco',
                                                section='Boleto'))
    if not has_bank or not has_section:
        warning(_(u"Looks like you didn't configure stoq yet to "
                   "generate bills. Check the manual to see how."))
        return False
    return True

class BillReport(object):
    def __init__(self, filename, payments):
        config = get_utility(IStoqConfig)
        bank_id = config.get_option('banco', section='Boleto')
        extra_args = {}
        for key, value in config.get_section_items(bank_id):
            extra_args[key] = value


        instructions = []
        for i in range(1, 4):
            inst = 'instrucao%s' % i
            if config.has_option(inst, section='Boleto'):
                instructions.append(config.get_option(inst,
                                                section='Boleto'))
        instructions.append(_('Stoq Retail Managment') + ' - www.stoq.com.br')
        extra_args['instrucoes'] = instructions

        demonstrativo = [payments[0].group.get_description()]
        sale = payments[0].group.sale
        if sale:
            for item in sale.get_items():
                demonstrativo.append(' - %s' % item.get_description())
        extra_args['demonstrativo'] = demonstrativo

        branch = payments[0].group.get_parent().branch
        extra_args['cedente'] = branch.get_description()

        address = payments[0].group.payer.get_main_address()
        extra_args['sacado'] = [payments[0].group.payer.name,
                                address.get_address_string(),
                                address.get_details_string()]


        format = BoletoPDF.FORMAT_BOLETO
        if len(payments) > 1:
            format = BoletoPDF.FORMAT_CARNE
        self.bill = BoletoPDF(filename, format)
        self.klass = get_bank(bank_id)
        for p in payments:
            if p.method.method_name != 'bill':
                continue
            self.add_payment(p, extra_args)

    def add_payment(self, payment, extra_args):
        data = self.klass(
            valor_documento=payment.value,
            data_vencimento=payment.due_date.date(),
            data_documento=payment.open_date.date(),
            data_processamento=datetime.date.today(),

            nosso_numero="%d" % payment.id,
            numero_documento="%d" % payment.id,

            **extra_args
        )

        self.bill.add_data(data)

    def save(self):
        self.bill.render()
        self.bill.save()
