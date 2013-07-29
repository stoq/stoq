# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

__tests__ = 'stoqlib/domain/payment/comment.py'

from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.domain.test.domaintest import DomainTest


class TestPaymentComment(DomainTest):
    def test_get_description(self):
        user = self.create_user()
        payment = self.create_payment()
        comment = PaymentComment(author=user, payment=payment,
                                 comment=u'Test de commentário')
        self.assertEquals(comment.get_description(), '[individual] Test de '
                                                     'commentário')
