# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012 Async Open Source
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

# This is mostly lifted from
# http://code.google.com/p/pyboleto licensed under MIT

import datetime
import decimal
import operator

from kiwi.currency import currency
from kiwi.datatypes import converter, ValidationError
from kiwi.python import Settable

from stoqlib.database.runtime import get_current_branch, get_connection
from stoqlib.lib.formatters import (format_phone_number, get_full_date,
                                    get_price_as_cardinal)
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import get_logotype_path
from stoqlib.reporting.report import HTMLReport

_ = stoqlib_gettext


class BookletReport(HTMLReport):
    title = _("Booklets")
    template_filename = "booklet/report.html"

    def __init__(self, filename, payments):
        self.booklets_data = list(self._get_booklets_data(payments))
        HTMLReport.__init__(self, filename)

    def _get_booklets_data(self, payments):
        payments = sorted(payments, key=operator.attrgetter('due_date'))
        n_total_inst = payments[0].group.installments_number

        conn = get_connection()
        logo_path = get_logotype_path(conn)
        branch = get_current_branch(conn)

        for i, payment in enumerate(payments):
            if payment.method.method_name != 'store_credit':
                continue

            group = payment.group
            sale = group.sale
            drawer_company = self._get_drawer(payment)
            drawer_person = drawer_company.person
            drawee_person = group.payer
            emission_address = branch.person.get_main_address()
            emission_location = emission_address.city_location

            if sale:
                sale_id = sale.get_order_number_str()
                total_value = self._format_currency(sale.get_total_sale_amount())
            else:
                # Support non-sale booklets
                sale_id = ''
                total_value = ''

            booklet = Settable(
                # FIXME: Rename id -> number
                sale_id=sale_id,
                payment_id=payment.get_payment_number_str(),
                installment=self._format_installment(payment.installment_number,
                                                     n_total_inst),
                emission_date=self._format_date(datetime.date.today()),
                emission_date_full=self._format_date(datetime.date.today(),
                                                     full=True),
                due_date=self._format_date(payment.due_date),
                due_date_full=self._format_date(payment.due_date, full=True),
                value=self._format_currency(payment.value),
                value_full=self._format_currency(payment.value, full=True),
                total_value=total_value,
                drawer=drawer_company.get_description(),
                drawee=drawee_person.name,
                drawer_document=self._get_person_document(drawer_person),
                drawee_document=self._get_person_document(drawee_person),
                drawee_phone_number=self._get_person_phone(drawee_person),
                drawee_address=self._get_person_address(drawee_person),
                drawer_address=self._get_person_address(drawer_person),
                instructions=self._get_instructions(payment),
                demonstrative=self._get_demonstrative(payment),
                emission_city=emission_location.city,
                logo_path=logo_path,
                )
            yield booklet

    #
    #  Private
    #

    def _get_instructions(self, payment):
        conn = payment.get_connection()
        instructions = sysparam(conn).BOOKLET_INSTRUCTIONS
        return instructions.split('\n')

    def _get_demonstrative(self, payment):
        demonstrative = []
        sale = payment.group.sale
        if sale:
            items = sale.get_items()
            has_decimal = any([item.quantity - int(item.quantity) != 0
                               for item in items])
            for item in items:
                quantity = item.quantity if has_decimal else int(item.quantity)
                demonstrative.append('%s x %s' % (quantity,
                                                  item.get_description()))

        return demonstrative

    def _get_drawer(self, payment):
        sale = payment.group.sale
        if sale and sale.branch:
            return sale.branch

        return sysparam(payment.get_connection()).MAIN_COMPANY

    def _get_person_document(self, person):
        if person.individual:
            return person.individual.cpf
        if person.company:
            return person.company.cnpj

        return ''

    def _get_person_phone(self, person):
        phone_number = format_phone_number(person.phone_number)
        mobile_number = format_phone_number(person.mobile_number)
        if phone_number and mobile_number:
            return '%s | %s' % (phone_number, mobile_number)

        return phone_number or mobile_number

    def _get_person_address(self, person):
        address = person.get_main_address()
        location = address.city_location
        return (address.get_address_string(),
                '%s / %s' % (location.city, location.state))

    def _format_installment(self, installment, total_installments):
        return _("%s of %s") % (installment, total_installments)

    def _format_currency(self, value, full=False):
        if isinstance(value, (int, float)):
            value = decimal.Decimal(value)

        if full:
            return get_price_as_cardinal(value)

        try:
            return converter.as_string(currency, value)
        except ValidationError:
            return ''

    def _format_date(self, date, full=False):
        if isinstance(date, datetime.datetime):
            date = date.date()

        if full:
            return get_full_date(date)

        try:
            return converter.as_string(datetime.date, date)
        except ValidationError:
            return ''

    def get_namespace(self):
        return dict(booklets=self.booklets_data)

    def adjust_for_test(self):
        for booklet_data in self.booklets_data:
            date = datetime.date(2012, 01, 01)
            booklet_data.emission_date = self._format_date(date)
            booklet_data.emission_date_full = self._format_date(date,
                                                                full=True)


def test():  # pragma nocover
    from stoqlib.domain.sale import Sale
    from stoqlib.api import api
    import sys
    creator = api.prepare_test()
    sale = Sale.selectOneBy(id=int(sys.argv[-1]), connection=creator.trans)
    r = BookletReport('teste.pdf', sale.payments)
    r.save_html('teste.html')
    r.save()

if __name__ == '__main__':  # pragma nocover
    test()
