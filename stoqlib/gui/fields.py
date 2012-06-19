# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
## Foundation, Outc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##


import gobject

from kiwi.ui.forms import ChoiceField

from stoqlib.api import api
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class DomainChoiceField(ChoiceField):
    editor = gobject.property(type=object)

    default_overrides = dict(can_add=True, can_edit=True)

    # Field

    def add_button_clicked(self, button):
        self._run_editor()

    def edit_button_clicked(self, button):
        self._run_editor(self.widget.get_selected())

    def content_changed(self):
        self.edit_button.set_sensitive(
            bool(self.widget.get_selected()))

    # Private

    def _run_editor(self, model=None):
        trans = api.new_transaction()
        model = trans.get(model)
        model = self.run_dialog(trans, model)
        rv = api.finish_transaction(trans, model)
        if rv:
            self.populate(model, trans)
            self.widget.select(model)
        trans.close()

    # Overrides

    def run_dialog(self, trans, model):
        raise NotImplementedError


class PaymentCategoryField(DomainChoiceField):
    category_type = gobject.property(type=object, default=None)

    def populate(self, value, trans):
        from stoqlib.domain.payment.category import PaymentCategory
        categories = PaymentCategory.selectBy(
            connection=trans,
            category_type=self.category_type).orderBy('name')
        values = api.for_combo(
            categories, empty=_('No category'), attr='name')
        self.widget.prefill(values)
        self.widget.select(value)
        # FIXME: Move to noun
        self.add_button.set_tooltip_text(_("Add a new payment category"))
        self.edit_button.set_tooltip_text(_("Edit the selected payment category"))
        self.edit_button.set_sensitive(False)
        self.widget.set_sensitive(bool(categories))

    def run_dialog(self, trans, category):
        from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(PaymentCategoryEditor, self, trans, category,
                          self.category_type)


class PersonField(DomainChoiceField):
    default_overrides = DomainChoiceField.default_overrides.copy()
    default_overrides.update(use_entry=True)

    person_type = gobject.property(type=object)

    def populate(self, person, trans):
        from stoqlib.domain.person import Client, Supplier, Transporter, SalesPerson
        person_type = self.person_type
        if person_type == Supplier:
            facets = person_type.get_active_suppliers(trans)
            self.add_button.set_tooltip_text(_("Add a new supplier"))
            self.edit_button.set_tooltip_text(_("Edit the selected supplier"))
        elif person_type == Client:
            facets = person_type.get_active_clients(trans)
            self.add_button.set_tooltip_text(_("Add a new client"))
            self.edit_button.set_tooltip_text(_("Edit the selected client"))
        elif person_type == Transporter:
            facets = person_type.get_active_transporters(trans)
            self.add_button.set_tooltip_text(_("Add a new transporter"))
            self.edit_button.set_tooltip_text(_("Edit the selected transporter"))
        elif person_type == SalesPerson:
            facets = person_type.get_active_salespersons(trans)
            self.add_button.set_tooltip_text(_("Add a new sales person"))
            self.edit_button.set_tooltip_text(_("Edit the selected sales person"))
        else:
            raise AssertionError(self.person_class)

        items = [(f.person.name, f) for f in facets]
        self.widget.prefill(items)
        self.widget.set_sensitive(bool(items))

        if person:
            facet = person_type.selectOneBy(
                person=person, connection=person.get_connection())
            self.widget.select(facet)

    def run_dialog(self, trans, person):
        from stoqlib.domain.person import Client, Supplier, Transporter
        from stoqlib.gui.editors.personeditor import (ClientEditor,
                                                      SupplierEditor,
                                                      TransporterEditor)
        editors = {
            Client: ClientEditor,
            Supplier: SupplierEditor,
            Transporter: TransporterEditor,
            }
        editor = editors.get(self.person_type)
        if editor is None:
            raise NotImplementedError(self.person_type)

        from stoqlib.gui.wizards.personwizard import run_person_role_dialog
        return run_person_role_dialog(editor, self, trans, person)
