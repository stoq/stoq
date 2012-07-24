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
    default_overrides = dict(has_add_button=True, has_edit_button=True)

    #: If we have the permission to add new object of this kind
    can_add = gobject.property(type=bool, default=True)

    #: If we have the permission to edit the currently selected object
    can_edit = gobject.property(type=bool, default=True)

    #: If we have the permission to view the details of the currently
    #: selected object
    can_view = gobject.property(type=bool, default=True)

    # Field

    def attach(self):
        self.connect('notify::can-add', self._on_can_add__notify)
        self.connect('notify::can-edit', self._on_can_edit__notify)
        self.connect('notify::can-view', self._on_can_view__notify)
        # Make sure we set the buttons state properly
        self._update_add_button_sensitivity()
        self._update_edit_button_sensitivity()

    def add_button_clicked(self, button):
        self._run_editor()

    def edit_button_clicked(self, button):
        self._run_editor(self.widget.get_selected())

    def content_changed(self):
        self._update_edit_button_sensitivity()

    # Private

    def _run_editor(self, model=None):
        trans = api.new_transaction()
        model = trans.get(model)
        model = self.run_dialog(trans, model)
        rv = api.finish_transaction(trans, model)
        if rv:
            self.populate(model, trans)
        trans.close()

    def _update_add_button_sensitivity(self):
        self.add_button.set_sensitive(self.can_add)

    def _update_edit_button_sensitivity(self):
        has_selected = bool(self.widget.get_selected())
        can_edit_or_view = self.can_edit or self.can_view
        self.edit_button.set_sensitive(has_selected and can_edit_or_view)

    def _on_can_add__notify(self, obj, pspec):
        self._update_add_button_sensitivity()

    def _on_can_edit__notify(self, obj, pspec):
        self._update_edit_button_sensitivity()

    def _on_can_view__notify(self, obj, pspec):
        self._update_edit_button_sensitivity()

    # Overrides

    def run_dialog(self, trans, model):
        raise NotImplementedError


class AddressField(DomainChoiceField):
    default_overrides = DomainChoiceField.default_overrides.copy()
    default_overrides.update(use_entry=True)

    #: The person the address belongs to, must be a :py:class:`stoqlib.domain.person.Person`
    person = gobject.property(type=object, default=None)

    # Field

    def attach(self):
        self.connect('notify::person', self._on_person__notify)
        super(AddressField, self).attach()

    def populate(self, address, trans):
        from stoqlib.domain.address import Address
        self.person = address.person if address else None
        addresses = Address.selectBy(
            connection=trans,
            person=self.person).orderBy('street')

        self.widget.prefill(api.for_combo(addresses))
        if address:
            self.widget.select(address)

        self.add_button.set_tooltip_text(_("Add a new address"))
        self.edit_button.set_tooltip_text(_("Edit the selected address"))

    def run_dialog(self, trans, address):
        from stoqlib.gui.editors.addresseditor import AddressEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(AddressEditor, self.toplevel, trans, self.person,
                          address, visual_mode=not self.can_edit)

    # Public

    def set_from_client(self, client):
        self.person = client.person
        self.populate(self.person.get_main_address(),
                      self.person.get_connection())

    # Private

    def _on_person__notify(self, obj, pspec):
        # An address needs a person to be created
        self.add_button.set_sensitive(bool(self.person))


class PaymentCategoryField(DomainChoiceField):
    #: This is the type of payment category we will display in this field, it
    #: it should either be PaymentCategory.TYPE_PAYABLE or
    #: PaymentCategory.TYPE_RECEIVABLE
    category_type = gobject.property(type=object, default=None)

    # Field

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

    def run_dialog(self, trans, category):
        from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(PaymentCategoryEditor, self.toplevel, trans, category,
                          self.category_type, visual_mode=not self.can_edit)


class PersonField(DomainChoiceField):
    default_overrides = DomainChoiceField.default_overrides.copy()
    default_overrides.update(use_entry=True)

    #: This is the type of person we will display in this field, it
    #: must be a class referencing a :py:class:`stoqlib.domain.person.Person`
    person_type = gobject.property(type=object)

    # Field

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

        self.widget.prefill(api.for_person_combo(facets))

        if person:
            assert isinstance(person, person_type)
            self.widget.select(person)

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
        return run_person_role_dialog(editor, self.toplevel, trans, person,
                                      visual_mode=not self.can_edit)
