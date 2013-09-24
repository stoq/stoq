# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import datetime

from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.report import HTMLReport

_ = stoqlib_gettext


class LoanReceipt(HTMLReport):
    title = _("Loan")
    template_filename = "loan/loan.html"

    def __init__(self, filename, loan):
        self.loan = loan
        super(LoanReceipt, self).__init__(filename)

    #
    #  Private
    #

    def _get_person_document(self, person):
        if person.individual:
            return person.individual.cpf
        if person.company:
            return person.company.cnpj

        return ''

    def _get_person_address(self, person):
        address = person.get_main_address()
        location = address.city_location
        return (address.get_address_string(),
                '%s / %s' % (location.city, location.state))

    #
    #  HTMLReport
    #

    def get_namespace(self):
        store = self.loan.store
        order_identifier = unicode(self.loan.identifier)
        print_promissory_note = api.sysparam.get_bool('PRINT_PROMISSORY_NOTE_ON_LOAN')
        branch = api.get_current_branch(store)
        drawer_person = self.loan.branch.person
        drawee_person = self.loan.client.person
        emission_address = branch.person.get_main_address()
        emission_location = emission_address.city_location

        promissory_data = Settable(
            order_identifier=order_identifier,
            payment_number=None,
            drawee=drawee_person.name,
            drawer=branch.get_description(),
            drawee_document=self._get_person_document(drawee_person),
            drawer_document=self._get_person_document(drawer_person),
            drawee_address=self._get_person_address(drawee_person),
            drawer_address=self._get_person_address(drawer_person),
            due_date=self.loan.expire_date,
            value=self.loan.get_total_amount(),
            emission_city=emission_location.city,
            emission_date=datetime.date.today(),
        )

        return dict(
            subtitle=_("Loan number: %s") % order_identifier,
            loan=self.loan,
            print_promissory_note=print_promissory_note,
            promissory_data=promissory_data,
        )

    def adjust_for_test(self):
        # today is mocked on test
        date = datetime.date.today()
        self.loan.expire_date = date
        self.loan.open_date = date
        self.loan.identifier = 666
        self.logo_data = 'logo.png'


if __name__ == '__main__':  # pragma nocover
    from stoqlib.domain.loan import Loan
    import sys
    creator = api.prepare_test()
    loan_ = creator.trans.find(Loan, id=int(sys.argv[-1])).one()
    r = LoanReceipt('test.pdf', loan_)
    r.save_html('test.html')
    r.save()
