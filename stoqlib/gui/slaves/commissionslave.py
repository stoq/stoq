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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Slaves for commissions  """

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.sellable import Sellable, SellableCategory


class CommissionSlave(BaseEditorSlave):
    """A slave for a sellable(product or service) commission source"""

    gladefile = 'CommissionDataSlave'
    model_type = Sellable
    proxy_widgets = ('commission_check_btn',
                     'commission_spin',
                     'commission_inst_spin')

    def change_label(self, new):
        self.commission_check_btn.set_label(new)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)
        self._setup_commissions()

    def on_confirm(self):
        source = self._get_source()
        if self.commission_check_btn.get_active():
            if source:
                self._delete_source(source)
        else:
            if source:
                self._update_source(source)
            else:
                self._create_source()

    def _get_source(self):
        sellable = self.model
        return self.store.find(CommissionSource, sellable=sellable).one()

    def _create_source(self):
        direct = self._get_direct_commission()
        inst = self._get_installments_commission()
        CommissionSource(direct_value=direct,
                         installments_value=inst,
                         sellable=self.model,
                         store=self.store)

    def _delete_source(self, source):
        self.store.remove(source)

    def _update_source(self, source):
        source.direct_value = self._get_direct_commission()
        source.installments_value = self._get_installments_commission()

    def _setup_commissions(self):
        self.commission_check_btn.set_active(True)
        source = self._get_source()
        if source:
            self.commission_check_btn.set_active(False)
            self.commission_spin.set_value(source.direct_value)
            self.commission_inst_spin.set_value(source.installments_value)
        else:
            self.commission_spin.set_value(0)
            self.commission_inst_spin.set_value(0)

    def _is_checked(self):
        return not self.commission_check_btn.get_active()

    def _get_direct_commission(self):
        return self.commission_spin.read()

    def _get_installments_commission(self):
        return self.commission_inst_spin.read()

    #
    # Kiwi callbacks
    #

    def on_commission_check_btn__content_changed(self, widget):
        can_active_spin = not widget.get_active()
        self.commission_spin.set_sensitive(can_active_spin)
        self.commission_inst_spin.set_sensitive(can_active_spin)


class CategoryCommissionSlave(CommissionSlave):
    """A slave for category commission source"""

    model_type = SellableCategory

    def _get_source(self):
        return self.store.find(CommissionSource, category=self.model).one()

    def _create_source(self):
        direct = self._get_direct_commission()
        inst = self._get_installments_commission()
        CommissionSource(direct_value=direct,
                         installments_value=inst,
                         category=self.model,
                         store=self.store)

    def on_commission_check_btn__content_changed(self, widget):
        CommissionSlave.on_commission_check_btn__content_changed(self, widget)

        if widget.get_active():
            category = self.model.category
            while category:
                cs = self.store.find(CommissionSource, category=category).one()
                if cs:
                    self.commission_spin.update(cs.direct_value)
                    self.commission_inst_spin.update(cs.installments_value)
                    break

                category = category.category
