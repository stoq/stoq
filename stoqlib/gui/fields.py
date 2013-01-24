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

import os
import tempfile

import gio
import gobject
import gtk
from kiwi.ui.dialogs import open as kiwi_open
from kiwi.ui.forms import ChoiceField, Field
import pango

from stoqlib.api import api
from stoqlib.domain.attachment import Attachment
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
        store = api.new_store()
        model = store.fetch(model)
        model = self.run_dialog(store, model)
        rv = store.confirm(model)
        if rv:
            self.populate(model, store)
        store.close()

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

    def run_dialog(self, store, model):
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

    def populate(self, address, store):
        from stoqlib.domain.address import Address
        self.person = address.person if address else None
        addresses = store.find(Address,
            person=self.person).order_by(Address.street)

        self.widget.prefill(api.for_combo(addresses))
        if address:
            self.widget.select(address)

        self.add_button.set_tooltip_text(_("Add a new address"))
        self.edit_button.set_tooltip_text(_("Edit the selected address"))

    def run_dialog(self, store, address):
        from stoqlib.gui.editors.addresseditor import AddressEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(AddressEditor, self.toplevel, store, self.person,
                          address, visual_mode=not self.can_edit)

    # Public

    def set_from_client(self, client):
        self.person = client.person
        self.populate(self.person.get_main_address(),
                      self.person.store)

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

    def populate(self, value, store):
        from stoqlib.domain.payment.category import PaymentCategory
        categories = PaymentCategory.get_by_type(store, self.category_type)
        values = api.for_combo(
            categories, empty=_('No category'), attr='name')
        self.widget.prefill(values)
        self.widget.select(value)
        # FIXME: Move to noun
        self.add_button.set_tooltip_text(_("Add a new payment category"))
        self.edit_button.set_tooltip_text(_("Edit the selected payment category"))

    def run_dialog(self, store, category):
        from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(PaymentCategoryEditor, self.toplevel, store, category,
                          self.category_type, visual_mode=not self.can_edit)


class PersonField(DomainChoiceField):
    default_overrides = DomainChoiceField.default_overrides.copy()
    default_overrides.update(use_entry=True)

    #: This is the type of person we will display in this field, it
    #: must be a class referencing a :py:class:`stoqlib.domain.person.Person`
    person_type = gobject.property(type=object)

    # Field

    def populate(self, person, store):
        from stoqlib.domain.person import (Client, Supplier, Transporter,
                                           SalesPerson, Branch)
        person_type = self.person_type
        if person_type == Supplier:
            objects = Supplier.get_active_suppliers(store)
            self.add_button.set_tooltip_text(_("Add a new supplier"))
            self.edit_button.set_tooltip_text(_("Edit the selected supplier"))
        elif person_type == Client:
            objects = Client.get_active_clients(store)
            self.add_button.set_tooltip_text(_("Add a new client"))
            self.edit_button.set_tooltip_text(_("Edit the selected client"))
        elif person_type == Transporter:
            objects = Transporter.get_active_transporters(store)
            self.add_button.set_tooltip_text(_("Add a new transporter"))
            self.edit_button.set_tooltip_text(_("Edit the selected transporter"))
        elif person_type == SalesPerson:
            objects = SalesPerson.get_active_salespersons(store)
            self.add_button.set_tooltip_text(_("Add a new sales person"))
            self.edit_button.set_tooltip_text(_("Edit the selected sales person"))
        elif person_type == Branch:
            objects = Branch.get_active_branches(store)
            self.add_button.set_tooltip_text(_("Add a new branch"))
            self.edit_button.set_tooltip_text(_("Edit the selected branch"))
        else:
            raise AssertionError(self.person_type)

        self.widget.prefill(api.for_person_combo(objects))

        if person:
            assert isinstance(person, person_type)
            self.widget.select(person)

    def run_dialog(self, store, person):
        from stoqlib.domain.person import Branch, Client, Supplier, Transporter
        from stoqlib.gui.editors.personeditor import (BranchEditor,
                                                      ClientEditor,
                                                      SupplierEditor,
                                                      TransporterEditor)
        editors = {
            Branch: BranchEditor,
            Client: ClientEditor,
            Supplier: SupplierEditor,
            Transporter: TransporterEditor,
            }
        editor = editors.get(self.person_type)
        if editor is None:
            raise NotImplementedError(self.person_type)

        from stoqlib.gui.wizards.personwizard import run_person_role_dialog
        return run_person_role_dialog(editor, self.toplevel, store, person,
                                      visual_mode=not self.can_edit)


class AttachmentField(Field):
    """This field allows attaching files to models.

      It has:
      * a button, which you can click if there's an attachment. The attachment
        will open in the default system application based on its mimetype
      * the add_button, which you can click to add an attachment in case
        there's none
      * the edit_button, which you can click to change an attachment
      * the delete_button, which you can click to delete an attachment

      It is the editor's responsibility to get the attachment and associate it
      to the model. For example:

         >>> self.model.attachment = self.fields['attachment'].attachment
    """
    widget_data_type = object

    has_add_button = True
    has_edit_button = True
    has_delete_button = True

    no_attachment_lbl = _('No attachment.')

    def build_widget(self):
        button = gtk.Button()
        button.connect('clicked', self._on_open_button__clicked)

        box = gtk.HBox(False, 4)
        button.add(box)

        self._label = gtk.Label(self.no_attachment_lbl)
        self._label.set_ellipsize(pango.ELLIPSIZE_END)
        self._label.set_alignment(0.5, 0.5)
        box.pack_start(self._label, True, True, 0)

        self.image = gtk.Image()
        box.pack_end(self.image, False, False, 0)

        self.sep = gtk.VSeparator()
        box.pack_start(self.sep, False, False, 0)

        button.show_all()

        return button

    def populate(self, attachment, store):
        self.store = store
        self.attachment = attachment
        self._update_widget()

    def _update_widget(self):
        has_attachment = bool(self.attachment and self.attachment.blob)

        if has_attachment:
            self._label.set_label(self.attachment.get_description())
            app_info = gio.app_info_get_default_for_type(
                                                      self.attachment.mimetype,
                                                      must_support_uris=False)
            if app_info:
                gicon = app_info.get_icon()
                self.image.set_from_gicon(gicon, gtk.ICON_SIZE_SMALL_TOOLBAR)
        else:
            self._label.set_label(self.no_attachment_lbl)

        can_open = bool(has_attachment and app_info)

        self._open_button__set_sensitive(can_open)
        self.add_button.set_sensitive(not has_attachment)
        self.edit_button.set_sensitive(has_attachment)
        self.delete_button.set_sensitive(has_attachment)

    def _open_button__set_sensitive(self, can_open):
        self.widget.set_sensitive(can_open)
        self.image.set_visible(can_open)
        self.sep.set_visible(can_open)

    def delete_button_clicked(self, button):
        self.attachment.blob = None
        self._update_widget()

    def add_button_clicked(self, button):
        self._update_attachment()

    def edit_button_clicked(self, button):
        self._update_attachment()

    def _update_attachment(self):
        filters = []

        ffilter = gtk.FileFilter()
        ffilter.set_name(_('All Files'))
        ffilter.add_pattern('*')
        filters.append(ffilter)

        # Generates filter for all images.
        ffilter = gtk.FileFilter()
        ffilter.set_name(_('All Images'))
        ffilter.add_pixbuf_formats()
        filters.append(ffilter)

        self._add_mimetype_filter(filters, _('PDF'), 'application/pdf')
        self._add_mimetype_filter(filters, _('Text'), 'text/plain')

        filename = kiwi_open(_("Select attachment"), None, filter=filters)

        if not filename:
            return

        data = open(filename, 'rb').read()
        mimetype = gio.content_type_guess(filename, data, True)[0]
        if self.attachment is None:
            self.attachment = Attachment(store=self.store)
        self.attachment.name = os.path.basename(filename)
        self.attachment.mimetype = mimetype
        self.attachment.blob = data
        self._update_widget()

    def _add_mimetype_filter(self, filters, name, mimetype):
        ffilter = gtk.FileFilter()
        ffilter.set_name(name)
        ffilter.add_mime_type(mimetype)
        filters.append(ffilter)

    def _on_open_button__clicked(self, widget):
        assert self.attachment
        assert self.attachment.blob

        name = '%s-%s' % ('stoq-attachment', self.attachment.get_description())
        with tempfile.NamedTemporaryFile(suffix=name, delete=False) as f:
            filename = f.name
            f.write(self.attachment.blob)

        gfile = gio.File(path=filename)
        app_info = gio.app_info_get_default_for_type(
            self.attachment.mimetype, False)
        app_info.launch([gfile])
