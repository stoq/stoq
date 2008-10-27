# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):    Ariqueli Tejada Fonseca     <aritf@async.com.br>
##               Evandro Vale Miquelito      <evandro@async.com.br>
##
"""Credit Provider editor
"""


from stoqlib.gui.editors.baseeditor import BaseEditorSlave

from stoqlib.domain.interfaces import ICreditProvider


class CreditProviderDetailsSlave(BaseEditorSlave):
    model_iface = ICreditProvider
    gladefile = 'CredProviderDetailsSlave'
    proxy_widgets = ('provider_id',
                     'short_name',
                     'open_contract_date',
                     'max_installments',
                     'payment_day',
                     'closing_day')

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    CreditProviderDetailsSlave.proxy_widgets)
