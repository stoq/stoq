# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
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

import os

from stoqlib.domain.certificate import Certificate
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _


class CertificateEditor(BaseEditor):
    size = (-1, -1)
    gladefile = 'CertificateEditor'
    model_type = Certificate
    model_name = _("Certificate")
    certificate_widgets = [
        'name',
        'type',
        'active',
    ]
    password_widgets = ['password']
    proxy_widgets = certificate_widgets + password_widgets

    #
    #  BaseEditor
    #

    def create_model(self, store):
        return Certificate(store=store)

    def setup_proxies(self):
        self.type.prefill([
            (v, k) for k, v in Certificate.types_str.items()])
        self.password.update(self.model.password.password)
        self.proxy = self.add_proxy(self.model, self.certificate_widgets)

        self._po = self.model.password
        self.add_proxy(self._po, self.password_widgets)
        if not self._po.password and self.edit_mode:
            self.ask_password.set_active(True)

        self._update_widgets()

    def validate_confirm(self):
        # TODO: We should validate the certificate by trying to communicate
        # with SEFAZ once and checking that it replies correctly
        if self.model.content is None:
            warning(_("No certificate selected"))
            return False

        active_certificates = Certificate.get_active_certs(self.store, exclude=self.model)
        if self.model.active and not active_certificates.is_empty():
            warning(_("There can be only one active certificate at a time"))
            return False

        return True

    def on_confirm(self):
        # Make sure to clear the password if the user chose to ask for it
        if (self.model.type == Certificate.TYPE_PKCS11 and
                self.ask_password.get_active()):
            self._po.password = None

        self.model.password = self._po

    #
    #  Private
    #

    def _update_widgets(self):
        if self.model.type == Certificate.TYPE_PKCS11:
            self.ask_password.set_sensitive(True)
            self.certificate_lbl.set_text(_("Token lib file (.so)"))
            self.password.set_sensitive(not self.ask_password.get_active())
        elif self.model.type == Certificate.TYPE_PKCS12:
            self.ask_password.set_sensitive(False)
            self.certificate_lbl.set_text(_("Certificate file"))
        else:
            raise AssertionError("Unknown certificate type")

    #
    #  Callbacks
    #

    def on_certificate_chooser__selection_changed(self, widget):
        filename = widget.get_filename()
        if filename:
            with open(filename, 'rb') as f:
                self.model.content = f.read()
                self.model.name = str(os.path.basename(filename))

            self.proxy.update('name')

    def after_type__content_changed(self, widget):
        self._update_widgets()

    def after_unmask__toggled(self, widget):
        self.password.set_property("visibility", widget.get_active())

    def after_ask_password__toggled(self, widget):
        self._update_widgets()
