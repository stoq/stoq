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

from kiwi.component import get_utility
from pyboleto.data import get_bank
from pyboleto.pdf import BoletoPDF

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.message import warning

_ = stoqlib_gettext


def can_generate_bill():
    config = get_utility(IStoqConfig)
    if config.get('Boleto', 'banco') is None:
        warning(_(u"Looks like you didn't configure stoq yet to "
                   "generate bills. Check the manual to see how."))
        return False
    return True


class BillReport(object):
    def __init__(self, filename, payments):
        self._payments = payments
        self._filename = filename

        self._payments_added = False
        self._config = get_utility(IStoqConfig)
        self._bank_id = self._config.get('Boleto', 'banco')
        self._bill = self._get_bill()
        self._render_class = get_bank(self._bank_id)

        # Reports need a title when printing
        self.title = _("Bill")

        self.today = datetime.datetime.today()

    def _get_bill(self):
        format = BoletoPDF.FORMAT_BOLETO
        if len(self._payments) > 1:
            format = BoletoPDF.FORMAT_CARNE
        return BoletoPDF(self._filename, format)

    def _get_instrucoes(self):
        instructions = []
        for i in range(1, 4):
            value = self._config.get('Boleto', 'instrucao%s' % i)
            if value is not None:
                instructions.append(value)
        instructions.append(_('Stoq Retail Managment') + ' - www.stoq.com.br')
        return instructions

    def _get_demonstrativo(self):
        payment = self._payments[0]
        demonstrativo = [payment.group.get_description()]
        sale = payment.group.sale
        if sale:
            for item in sale.get_items():
                demonstrativo.append(' - %s' % item.get_description())
        return demonstrativo

    def _get_sacado(self):
        payment = self._payments[0]
        payer = payment.group.payer
        address = payer.get_main_address()
        return [payer.name,
                address.get_address_string(),
                address.get_details_string()]

    def _get_cedente(self):
        payment = self._payments[0]
        branch = payment.group.get_parent().branch
        return branch.get_description()

    def add_payments(self):
        if self._payments_added:
            return
        for p in self._payments:
            if p.method.method_name != 'bill':
                continue
            self._add_payment(p)
        self._payments_added = True

    def _add_payment(self, payment):
        kwargs = dict(
            valor_documento=payment.value,
            data_vencimento=payment.due_date.date(),
            data_documento=payment.open_date.date(),
            data_processamento=self.today,
            nosso_numero=str(payment.id),
            numero_documento=str(payment.id),
            sacado=self._get_sacado(),
            cedente=self._get_cedente(),
            demonstrativo=self._get_demonstrativo(),
            instrucoes=self._get_instrucoes(),
        )
        kwargs.update(self._config.items(self._bank_id))
        self.args = kwargs

    def override_payment_id(self, payment_id):
        self.args['nosso_numero'] = str(payment_id)
        self.args['numero_documento'] = str(payment_id)

    def override_payment_description(self, description):
        self.args['demonstrativo'] = description

    def save(self):
        self.add_payments()
        data = self._render_class(**self.args)
        self._bill.add_data(data)
        self._bill.render()
        self._bill.save()
