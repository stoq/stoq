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

"""

import datetime

from pyboleto.data import get_bank
from pyboleto.pdf import BoletoPDF
from kiwi.log import Logger

from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
log = Logger('stoqlib.lib.boleto')


(BILL_OPTION_BANK_BRANCH,
 BILL_OPTION_BANK_ACCOUNT,
 BILL_OPTION_CUSTOM) = range(3)


class BankInfo(object):
    def __init__(self, description, number, fields):
        self.description = description
        self.bank_number = number
        self.fields = fields

    def get_extra_fields(self):
        rv = []
        for field, kind in self.fields.items():
            if kind == BILL_OPTION_CUSTOM:
                rv.append(field)
        return rv

_banks = [
    BankInfo("Generic", None, {}),
    BankInfo('Banco Bradesco', 237,
             {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    BankInfo("Banco do Brasil", 1,
             {'convenio': BILL_OPTION_CUSTOM,
              'len_convenio': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    BankInfo('Banco Itau', 341,
             {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    BankInfo('Banco Real', 356,
             {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    # FIXME: Santander does not use 'agencia'
    BankInfo('Banco Santander', 33,
             {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    BankInfo('Caixa Econonima Federal', 104,
             {'carteira': BILL_OPTION_CUSTOM,
              'agencia': BILL_OPTION_BANK_BRANCH,
              'conta': BILL_OPTION_BANK_BRANCH}),
    ]


def get_all_banks():
    return _banks


def get_bank_info_by_number(number):
    for bank in _banks:
        if bank.bank_number == number:
            return bank


class BillReport(object):
    def __init__(self, filename, payments):
        self._payments = payments
        self._filename = filename

        self._payments_added = False
        # Reports need a title when printing
        self.title = _("Bill")

        self.today = datetime.datetime.today()

    @classmethod
    def check_printable(cls, payments):
        for payment in payments:
            msg = cls.validate_payment_for_printing(payment)
            if msg:
                warning(_("Could not print Bill Report"),
                        description=msg)
                return False

        return True

    @classmethod
    def validate_payment_for_printing(cls, payment):
        account = payment.method.destination_account
        if not account:
            msg = _("Payment method missing a destination account: '%s'" % (
                account.description, ))
            return msg

        from stoqlib.domain.account import Account
        if (account.account_type != Account.TYPE_BANK or
            not account.bank):
            msg = _("Account '%s' must be a bank account.\n"
                    "You need to configure the bill payment method in "
                    "the admin application and try again" % (account.description, ))
            return msg

        bank = account.bank
        if bank.bank_number == 0:
            msg = _("Improperly configured bank account: %r" % (bank, ))
            return msg

        # FIXME: Verify that all bill option fields are configured properly

        bank_no = bank.bank_number
        bank_info = get_bank_info_by_number(bank_no)
        if not bank_info:
            msg = _("Missing stoq support for bank %d" % (bank_no, ))
            return msg

        boleto_bank = get_bank('%03d' % (bank_no,))
        if not boleto_bank:
            msg = _("Missing pyboleto support for %d" % (bank_no, ))
            return msg

    def _get_bill(self):
        format = BoletoPDF.FORMAT_BOLETO
        if len(self._payments) > 1:
            format = BoletoPDF.FORMAT_CARNE
        return BoletoPDF(self._filename, format)

    def _get_instrucoes(self, payment):
        instructions = []
        data = sysparam(payment.get_connection()).BILL_INSTRUCTIONS
        for line in data.split('\n')[:3]:
            line = line.replace('$DATE', payment.due_date.strftime('%d/%m/%Y'))
            instructions.append(line)

        instructions.append('\n' + _('Stoq Retail Managment') + ' - www.stoq.com.br')
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
        account = payment.method.destination_account
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
            instrucoes=self._get_instrucoes(payment),
            agencia=account.bank.bank_branch,
            conta=account.bank.bank_account,
        )
        for opt in account.bank.options:
            kwargs[opt.option] = opt.value
        self._bill = self._get_bill()
        self._render_class = get_bank('%03d' % (account.bank.bank_number, ))
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
