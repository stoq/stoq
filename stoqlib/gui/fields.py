# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012-2013 Async Open Source <http://www.async.com.br>
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

import datetime
import os
import tempfile

import gio
import gobject
import gtk
from kiwi.ui.dialogs import selectfile
from kiwi.ui.entry import ENTRY_MODE_DATA
from kiwi.ui.forms import TextField, ChoiceField, Field
import pango

from stoqlib.api import api
from stoqlib.domain.attachment import Attachment
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.utils.filters import get_filters_for_attachment
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.message import yesno

_ = stoqlib_gettext


def get_store_for_field(field):
    """Returns the store being used on the editor *field* is attached"""
    if not isinstance(field, Field):
        raise TypeError("field must be a Field subclass, not %s" % (field, ))

    toplevel = field.toplevel
    if not toplevel:
        raise TypeError("Field %r must be attached to a form" % (field, ))
    if not isinstance(toplevel, BaseEditorSlave):
        raise TypeError("Field %r must be attached to a BaseEditorSlave "
                        "subclass, not %r" % (field, toplevel.__class__.__name__))

    return toplevel.store


class DomainChoiceField(ChoiceField):
    """Field used to select a domain object

    The graphical interface for it contains::

      * a combobox entry for selecting the model object
      * an add_button, which you can click to add a new object
        to the model. It's sensitivity is controller by :obj:`.can_add`
      * an edit_button, which you can click to edit the selected
        object. It's sensitivity is controlled by :obj:`.can_edit` and
        :obj:`.can_view`.

    It's supposed to be subclassed and have it's :meth:`.populate` and
    :meth:`.run_dialog` implemented on the subclass

    """
    default_overrides = dict(has_add_button=True, has_edit_button=True)

    #: If we have the permission to add new object of this kind
    can_add = gobject.property(type=bool, default=True)

    #: If we have the permission to edit the currently selected object
    can_edit = gobject.property(type=bool, default=True)

    #: If we have the permission to view the details of the currently
    #: selected object
    can_view = gobject.property(type=bool, default=True)

    #: If we are using the ids to pupulate the field instead of domain
    #: objects. This changes what gets send as argument on :meth:`.populate`
    #: after :attr:`._run_editor` is called
    use_ids = False

    # Field

    def prefill(self, items, value=None):
        self.widget.prefill(items)
        if value is not None:
            self.widget.select(value)

        if self.use_entry:
            # FIXME: Make sure the entry is set to data mode or else ir will
            # allow any string to be typed when items is empty. This is because
            # kiwi will only set data mode on the entry when it gets prefilled
            # with a list of tuples. We should improve that code to avoid this
            # kind of workarounds
            self.widget.entry.set_mode(ENTRY_MODE_DATA)

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
            if self.use_ids:
                value = model.id
            else:
                main_store = get_store_for_field(self)
                value = main_store.fetch(model)
            self.populate(value)
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

    def populate(self, address):
        from stoqlib.domain.address import Address
        self.person = address.person if address else None
        store = get_store_for_field(self)
        addresses = store.find(Address,
                               person=self.person).order_by(Address.street)

        self.prefill(api.for_combo(addresses), address)

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
        self.populate(self.person.get_main_address())

    # Private

    def _on_person__notify(self, obj, pspec):
        # An address needs a person to be created
        self.add_button.set_sensitive(bool(self.person))


class PaymentMethodField(ChoiceField):
    #: The type of the payment used to get creatable methods.
    #: See :meth:`stoqlib.lib.interfaces.IPaymentOperation.creatable`
    #: for more information
    payment_type = gobject.property(type=object, default=None)

    #: If this is being created separated from a |sale| / |purchase|
    #: See :meth:`stoqlib.lib.interfaces.IPaymentOperation.creatable`
    #: for more information
    separate = gobject.property(type=bool, default=True)

    # Field

    def populate(self, value):
        from stoqlib.domain.payment.method import PaymentMethod
        assert self.payment_type is not None
        store = get_store_for_field(self)
        methods = set(PaymentMethod.get_creatable_methods(
            store, self.payment_type, separate=self.separate))
        # Add the current value, just in case the payment method is not
        # currently creatable
        methods.add(value)
        self.widget.prefill(api.for_combo(methods))
        if value is not None:
            self.widget.select(value)


class PaymentCategoryField(DomainChoiceField):
    #: This is the type of payment category we will display in this field, it
    #: it should either be PaymentCategory.TYPE_PAYABLE or
    #: PaymentCategory.TYPE_RECEIVABLE
    category_type = gobject.property(type=object, default=None)

    # Field

    def populate(self, value):
        from stoqlib.domain.payment.category import PaymentCategory
        store = get_store_for_field(self)
        categories = PaymentCategory.get_by_type(store, self.category_type)
        values = api.for_combo(
            categories, empty=_('No category'), attr='name')
        self.prefill(values, value)
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
    use_ids = True

    #: This is the type of person we will display in this field, it
    #: must be a class referencing a :py:class:`stoqlib.domain.person.Person`
    person_type = gobject.property(type=object)

    # Field

    def populate(self, person_id):
        from stoqlib.domain.person import (Client, Supplier, Transporter,
                                           SalesPerson, Branch)
        store = get_store_for_field(self)
        person_type = self.person_type
        if person_type == Supplier:
            self.add_button.set_tooltip_text(_("Add a new supplier"))
            self.edit_button.set_tooltip_text(_("Edit the selected supplier"))
        elif person_type == Client:
            self.add_button.set_tooltip_text(_("Add a new client"))
            self.edit_button.set_tooltip_text(_("Edit the selected client"))
        elif person_type == Transporter:
            self.add_button.set_tooltip_text(_("Add a new transporter"))
            self.edit_button.set_tooltip_text(_("Edit the selected transporter"))
        elif person_type == SalesPerson:
            self.add_button.set_tooltip_text(_("Add a new sales person"))
            self.edit_button.set_tooltip_text(_("Edit the selected sales person"))
        elif person_type == Branch:
            self.add_button.set_tooltip_text(_("Add a new branch"))
            self.edit_button.set_tooltip_text(_("Edit the selected branch"))
        else:
            raise AssertionError(self.person_type)

        items = person_type.get_active_items(store)
        self.prefill(items, person_id)

    def run_dialog(self, store, person):
        from stoqlib.domain.person import (Branch, Client, Supplier,
                                           Transporter, SalesPerson)
        from stoqlib.gui.editors.personeditor import (BranchEditor,
                                                      ClientEditor,
                                                      EmployeeEditor,
                                                      SupplierEditor,
                                                      TransporterEditor)
        editors = {
            Branch: BranchEditor,
            Client: ClientEditor,
            Supplier: SupplierEditor,
            Transporter: TransporterEditor,
            SalesPerson: EmployeeEditor,
        }
        editor = editors.get(self.person_type)
        if editor is None:  # pragma no cover
            raise NotImplementedError(self.person_type)

        # FIXME: Salesperson is edited on EmployeeEditor, so we need to get
        # that facet for the editor
        if isinstance(person, SalesPerson):
            person = person.person.employee

        from stoqlib.gui.wizards.personwizard import run_person_role_dialog
        return run_person_role_dialog(editor, self.toplevel, store, person,
                                      visual_mode=not self.can_edit)

    def edit_button_clicked(self, button):
        facet_id = self.widget.get_selected()
        store = get_store_for_field(self)
        facet = store.get(self.person_type, facet_id)
        self._run_editor(facet)


class PersonQueryField(TextField):

    default_overrides = dict(has_add_button=True)

    #: This is the type of person we will display in this field, it
    #: must be a class referencing a :py:class:`stoqlib.domain.person.Person`
    person_type = gobject.property(type=object)

    widget_data_type = object

    def attach(self):
        assert self.editable

        from stoqlib.domain.person import Client, Supplier
        from stoqlib.gui.widgets.queryentry import (ClientEntryGadget,
                                                    SupplierEntryGadget)
        gadgets = {
            Client: ClientEntryGadget,
            Supplier: SupplierEntryGadget,
        }
        gadget = gadgets.get(self.person_type)
        if gadgets is None:  # pragma no cover
            raise NotImplementedError(self.person_type)

        self.gadget = gadget(
            entry=self.widget,
            store=get_store_for_field(self),
            parent=self.toplevel,
            edit_button=self.add_button)

    def populate(self, obj):
        self.set_value(obj)

    def set_value(self, obj):
        self.gadget.set_value(obj)

    def add_button_clicked(self, button):
        # The gadget will take care of the callback. We just need to override
        # this to avoid a NotImplementedError
        pass


class CfopField(DomainChoiceField):
    """A domain choice field for selecting a |cfop|

    More information about this class on :class:`DomainChoiceField`
    """

    default_overrides = DomainChoiceField.default_overrides.copy()
    default_overrides.update(use_entry=True, can_edit=False)

    # Field

    def populate(self, cfop):
        from stoqlib.domain.fiscal import CfopData
        store = get_store_for_field(self)
        cfops = store.find(CfopData)
        self.prefill(api.for_combo(cfops), cfop)

        self.add_button.set_tooltip_text(_("Add a new C.F.O.P"))
        self.edit_button.set_tooltip_text(_("View C.F.O.P details"))

    def run_dialog(self, store, cfop):
        from stoqlib.gui.editors.fiscaleditor import CfopEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(CfopEditor, self.toplevel, store, cfop,
                          visual_mode=not self.can_edit)


class GridGroupField(DomainChoiceField):
    """A domain choice field for selecting a |gridgroup|

    More information about this class on :class:`DomainChoiceField`
    """

    # Field

    def populate(self, gridgroup):
        from stoqlib.domain.product import GridGroup
        store = get_store_for_field(self)
        self.prefill(api.for_combo(store.find(GridGroup)), gridgroup)

        self.add_button.set_tooltip_text(_("Add a new grid group"))
        self.edit_button.set_tooltip_text(_("Edit the grid group"))

    def run_dialog(self, store, gridgroup):
        from stoqlib.gui.editors.grideditor import GridGroupEditor
        from stoqlib.gui.base.dialogs import run_dialog
        return run_dialog(GridGroupEditor, None, store, gridgroup,
                          visual_mode=not self.can_edit)


class AttachmentField(Field):
    """This field allows attaching files to models.

      The graphical interface for it contains:

        * a button, which you can click if there's an attachment. The attachment
          will open in the default system application based on its mimetype
        * the add_button, which you can click to add an attachment in case
          there's none
        * the edit_button, which you can click to change an attachment
        * the delete_button, which you can click to delete an attachment

      It is the editor's responsibility to get the attachment and associate it
      to the model. For example::

         self.model.attachment = self.fields['attachment'].attachment
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

    def populate(self, attachment):
        self.store = get_store_for_field(self)
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
        if not yesno(_("Are you sure you want to remove the attachment?"),
                     gtk.RESPONSE_NO, _("Remove"), _("Don't remove")):
            return

        self.attachment.blob = None
        self._update_widget()

    def add_button_clicked(self, button):
        self._update_attachment()

    def edit_button_clicked(self, button):
        self._update_attachment()

    def _update_attachment(self):
        filters = get_filters_for_attachment()
        with selectfile(_("Select attachment"), filters=filters) as sf:
            rv = sf.run()
            filename = sf.get_filename()
            if rv != gtk.RESPONSE_OK or not filename:
                return

        data = open(filename, 'rb').read()
        mimetype = gio.content_type_guess(filename, data, False)
        if self.attachment is None:
            self.attachment = Attachment(store=self.store)
        self.attachment.name = unicode(os.path.basename(filename))
        self.attachment.mimetype = unicode(mimetype)
        self.attachment.blob = data
        self._update_widget()

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


class DateTextField(TextField):

    # FIXME: Maybe we should change kiwi to transform widget_data_type in a
    # gobject property so we can inform it at creation time
    widget_data_type = datetime.date
