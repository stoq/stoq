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
import operator

from kiwi.python import Settable

from stoqlib.database.runtime import get_current_branch, get_default_store
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import HTMLReport

_ = stoqlib_gettext


class BookletReport(HTMLReport):
    title = _("Booklets")
    template_filename = "booklet/report.html"

    def __init__(self, filename, payments):
        self.booklets_data = list(self._get_booklets_data(payments))
        HTMLReport.__init__(self, filename)

    #
    #  Private
    #

    def _get_booklets_data(self, payments):
        payments = sorted(payments, key=operator.attrgetter('due_date'))
        n_total_inst = payments[0].group.installments_number

        default_store = get_default_store()
        branch = get_current_branch(default_store)

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
                order_identifier = unicode(sale.identifier)
                total_value = sale.get_total_sale_amount()
            else:
                # Support non-sale booklets
                order_identifier = ''
                total_value = None

            booklet = Settable(
                order_identifier=order_identifier,
                payment_number=unicode(payment.identifier),
                installment=self._format_installment(payment.installment_number,
                                                     n_total_inst),
                emission_date=datetime.date.today(),
                due_date=payment.due_date,
                value=payment.value,
                total_value=total_value,
                drawer=drawer_company.get_description(),
                drawee=drawee_person.name,
                drawer_document=self._get_person_document(drawer_person),
                drawee_document=self._get_person_document(drawee_person),
                drawee_phone_number=self._get_person_phone(drawee_person),
                drawee_address=self._get_person_address(drawee_person),
                drawer_address=self._get_person_address(drawer_person),
                instructions=self._get_instructions(),
                demonstrative=self._get_demonstrative(payment),
                emission_city=emission_location.city,
            )
            yield booklet

    def _get_instructions(self):
        instructions = sysparam.get_string('BOOKLET_INSTRUCTIONS')
        return instructions.split('\n')

    def _get_demonstrative(self, payment):
        demonstrative = []
        sale = payment.group.sale
        if sale:
            items = sale.get_items()
            has_decimal = any([item.quantity - int(item.quantity) != 0
                               for item in items])
            for item in sorted(items,
                               key=operator.attrgetter('sellable.description')):
                quantity = item.quantity if has_decimal else int(item.quantity)
                demonstrative.append('%s x %s' % (quantity,
                                                  item.get_description()))

        return demonstrative

    def _get_drawer(self, payment):
        sale = payment.group.sale
        if sale and sale.branch:
            return sale.branch

        return sysparam.get_object(payment.store, 'MAIN_COMPANY')

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

    #
    #  HTMLReport
    #

    def get_namespace(self):
        promissory_notes = sysparam.get_bool('PRINT_PROMISSORY_NOTES_ON_BOOKLETS')
        return dict(booklets=self.booklets_data,
                    promissory_notes=promissory_notes)

    def adjust_for_test(self):
        for booklet_data in self.booklets_data:
            booklet_data.emission_date = datetime.date(2012, 01, 01)


def test():  # pragma nocover
    from stoqlib.domain.sale import Sale
    from stoqlib.api import api
    import sys
    creator = api.prepare_test()
    sale = creator.store.find(Sale, id=int(sys.argv[-1])).one()
    r = BookletReport('teste.pdf', sale.payments)
    r.save_html('teste.html')
    r.save()

if __name__ == '__main__':  # pragma nocover
    test()
