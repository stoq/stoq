# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
"""Company template editor"""

from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.domain.interfaces import ICompany
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class CompanyDocumentsSlave(BaseEditorSlave):
    model_iface = ICompany
    gladefile = 'CompanyDocumentsSlave'
    proxy_widgets = ('cnpj',
                     'fancy_name',
                     'state_registry',
                     'city_registry')

    def setup_proxies(self):
        self.document_l10n = api.get_l10n_field(self.conn, 'company_document')
        self.cnpj_lbl.set_label(self.document_l10n.label)
        self.cnpj.set_mask(self.document_l10n.entry_mask)
        self.proxy = self.add_proxy(self.model,
                                    CompanyDocumentsSlave.proxy_widgets)

    def on_cnpj__validate(self, widget, value):
        # This will allow the user to use an empty value to this field
        if self.cnpj.is_empty():
            return

        if not self.document_l10n.validate(value):
            return ValidationError(_('%s is not valid.') % (
                self.document_l10n.label,))

        if self.model.check_cnpj_exists(value):
            return ValidationError(
                _('A company with this %s already exists') % (
                self.document_l10n.label))


class CompanyEditorTemplate(BaseEditorSlave):
    model_iface = ICompany
    gladefile = 'BaseTemplate'

    def __init__(self, conn, model=None, person_slave=None,
                 visual_mode=False):
        self._person_slave = person_slave
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def get_person_slave(self):
        return self._person_slave

    def attach_person_slave(self, slave):
        self._person_slave.attach_slave('person_status_holder', slave)

    #
    # BaseEditor hooks
    #

    def setup_slaves(self):
        self.company_docs_slave = CompanyDocumentsSlave(
            self.conn, self.model, visual_mode=self.visual_mode)
        self._person_slave.attach_slave('company_holder',
                                       self.company_docs_slave)

    def on_confirm(self, confirm_person=True):
        if confirm_person:
            self._person_slave.on_confirm()
        return self.model
