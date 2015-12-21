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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Templates implementation for person editors.  """

import gtk

from stoqlib.domain.person import Company, Individual, Person, Supplier
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.slaves import NoteSlave
from stoqlib.gui.dialogs.addressdialog import AddressAdditionDialog
from stoqlib.gui.dialogs.contactsdialog import ContactInfoListDialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.search.callsearch import CallsSearch
from stoqlib.gui.search.creditcheckhistorysearch import CreditCheckHistorySearch
from stoqlib.gui.slaves.addressslave import AddressSlave
from stoqlib.gui.templates.companytemplate import CompanyEditorTemplate
from stoqlib.gui.templates.individualtemplate import IndividualEditorTemplate
from stoqlib.gui.utils.databaseform import DatabaseForm
from stoqlib.lib.message import warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _PersonEditorTemplate(BaseEditorSlave):
    model_type = Person
    gladefile = 'PersonEditorTemplate'

    proxy_widgets = ('name',
                     'phone_number',
                     'fax_number',
                     'mobile_number',
                     'email')

    def __init__(self, store, model, visual_mode, ui_form_name, parent):
        self._parent = parent
        if ui_form_name:
            self.db_form = DatabaseForm(ui_form_name)
        else:
            self.db_form = None

        super(_PersonEditorTemplate, self).__init__(store, model,
                                                    visual_mode=visual_mode)

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, store):
        return Person(name=u"", store=store)

    def setup_proxies(self):
        self._setup_widgets()
        self._setup_form_fields()
        self.proxy = self.add_proxy(self.model,
                                    _PersonEditorTemplate.proxy_widgets)

    def setup_slaves(self):
        self.address_slave = AddressSlave(
            self.store, self.model, self.model.get_main_address(),
            visual_mode=self.visual_mode,
            db_form=self.db_form)
        self.attach_slave('address_holder', self.address_slave)
        self.attach_model_slave('note_holder', NoteSlave, self.model)

    def on_confirm(self):
        main_address = self.address_slave.model
        main_address.person = self.model

    #
    # Public API
    #

    def add_extra_tab(self, tab_label, slave, position=None):
        """Adds an extra tab to the editor

        :param tab_label: the label that will be display on the tab
        :param slave: the slave that will be attached to the new tab
        :param position: the position the tab will be attached
        """
        event_box = gtk.EventBox()
        self.person_notebook.append_page(event_box, gtk.Label(tab_label))
        self.attach_slave(tab_label, slave, event_box)
        event_box.show()

        if position is not None:
            self.person_notebook.reorder_child(event_box, position)
            self.person_notebook.set_current_page(position)

    def attach_role_slave(self, slave):
        self.attach_slave('role_holder', slave)

    def attach_model_slave(self, name, slave_type, slave_model):
        slave = slave_type(self.store, slave_model,
                           visual_mode=self.visual_mode)
        self.attach_slave(name, slave)
        return slave

    #
    # Kiwi handlers
    #

    def on_name__map(self, entry):
        self.name.grab_focus()

    def on_address_button__clicked(self, button):
        main_address = self.model.get_main_address()
        if not main_address.is_valid_model():
            msg = _(u"You must define a valid main address before\n"
                    "adding additional addresses")
            warning(msg)
            return

        result = run_dialog(AddressAdditionDialog, self._parent,
                            self.store, person=self.model,
                            reuse_store=not self.visual_mode)
        if not result:
            return

        new_main_address = self.model.get_main_address()
        if new_main_address is not main_address:
            self.address_slave.set_model(new_main_address)

    def on_contact_info_button__clicked(self, button):
        run_dialog(ContactInfoListDialog, self._parent, self.store,
                   person=self.model, reuse_store=not self.visual_mode)

    def on_calls_button__clicked(self, button):
        run_dialog(CallsSearch, self._parent, self.store,
                   person=self.model, reuse_store=not self.visual_mode)

    def on_credit_check_history_button__clicked(self, button):
        run_dialog(CreditCheckHistorySearch, self._parent, self.store,
                   client=self.model.client, reuse_store=not self.visual_mode)

    #
    # Private API
    #

    def _setup_widgets(self):
        individual = self.model.individual
        company = self.model.company
        if not (individual or company):
            raise DatabaseInconsistency('A person must have at least a '
                                        'company or an individual set.')
        tab_child = self.person_data_tab
        if individual and company:
            tab_text = _('Individual/Company Data')
            self.company_frame.set_label(_('Company Data'))
            self.company_frame.show()
            self.individual_frame.set_label(_('Individual Data'))
            self.individual_frame.show()
        elif individual:
            tab_text = _('Individual Data')
            self.company_frame.hide()
            label_widget = self.individual_frame.get_label_widget()
            if label_widget is not None:
                label_widget.hide()
            self.individual_frame.show()
        else:
            tab_text = _('Company Data')
            self.individual_frame.hide()
            label_widget = self.company_frame.get_label_widget()
            if label_widget is not None:
                label_widget.hide()
            self.company_frame.show()
        self.person_notebook.set_tab_label_text(tab_child, tab_text)
        addresses = self.model.get_total_addresses()
        if addresses == 2:
            self.address_button.set_label(_("1 More Address..."))
        elif addresses > 2:
            self.address_button.set_label(_("%i More Addresses...")
                                          % (addresses - 1))
        if not self.model.client:
            self.credit_check_history_button.hide()

    def _setup_form_fields(self):
        if not self.db_form:
            return
        self.db_form.update_widget(self.name,
                                   other=self.name_lbl)
        self.db_form.update_widget(self.phone_number,
                                   other=self.phone_number_lbl)
        self.db_form.update_widget(self.fax_number, u'fax',
                                   other=self.fax_lbl)
        self.db_form.update_widget(self.email,
                                   other=self.email_lbl)
        self.db_form.update_widget(self.mobile_number,
                                   other=self.mobile_lbl)


class BasePersonRoleEditor(BaseEditor):
    """A base class for person role editors. This class can not be
    instantiated directly.

    :attribute main_slave:
    :attribute individual_slave:
    :attribute company_slave:
    :cvar help_section: the help button for this wizard,
      usually describing how to create a new person
    """
    size = (-1, -1)
    help_section = None
    ui_form_name = None
    need_cancel_confirmation = True

    def __init__(self, store, model=None, role_type=None, person=None,
                 visual_mode=False, parent=None, document=None, description=None):
        """ Creates a new BasePersonRoleEditor object

        :param store: a store
        :param model:
        :param none_type: None, ROLE_INDIVIDUAL or ROLE_COMPANY
        :param person:
        :param visual_mode:
        """
        if not (model or role_type is not None):
            raise ValueError('A role_type attribute is required')
        self._description = description
        self._parent = parent
        self.individual_slave = None
        self.company_slave = None
        self._person_slave = None
        self.main_slave = None
        self.role_type = role_type
        self.person = person
        self.document = document

        BaseEditor.__init__(self, store, model, visual_mode=visual_mode)
        # FIXME: Implement and use IDescribable on the model
        self.set_description(self.model.person.name)

    #
    # BaseEditor hooks
    #

    def create_model(self, store):
        # XXX: Waiting fix for bug 2163. We should not need anymore to
        # provide empty values for mandatory attributes
        if not self.person:
            self.person = Person(name=self._description or u'', store=store)
        if not self.role_type in [Person.ROLE_INDIVIDUAL,
                                  Person.ROLE_COMPANY]:
            raise ValueError("Invalid value for role_type attribute, %r" % (
                self.role_type, ))
        if (self.role_type == Person.ROLE_INDIVIDUAL and
            not self.person.individual):
            Individual(person=self.person, store=store, cpf=self.document)
        elif (self.role_type == Person.ROLE_COMPANY and
              not self.person.company):
            Company(person=self.person, store=store, cnpj=self.document)
        else:
            pass
        return self.person

    def setup_slaves(self):
        individual = self.model.person.individual
        company = self.model.person.company
        assert individual or company

        self._person_slave = _PersonEditorTemplate(self.store,
                                                   self.model.person,
                                                   visual_mode=self.visual_mode,
                                                   ui_form_name=self.ui_form_name,
                                                   parent=self._parent or self)

        if individual:
            slave = IndividualEditorTemplate(self.store,
                                             model=individual,
                                             person_slave=self._person_slave,
                                             visual_mode=self.visual_mode)
            self.individual_slave = slave
            self.main_slave = slave

        if company:
            slave = CompanyEditorTemplate(self.store,
                                          model=company,
                                          person_slave=self._person_slave,
                                          visual_mode=self.visual_mode)
            self.company_slave = slave
            self.main_slave = slave

        self.attach_slave('main_holder', slave)
        self.main_slave.attach_slave('main_holder', self._person_slave)

    def on_confirm(self):
        if (isinstance(self.model, Supplier) and
            not sysparam.has_object('SUGGESTED_SUPPLIER')):
            sysparam.set_object(self.store, 'SUGGESTED_SUPPLIER', self.model)

    #
    # Public API
    #

    def get_person_slave(self):
        return self._person_slave

    def set_phone_number(self, phone_number):
        slave = self.get_person_slave()
        slave.set_phone_number(phone_number)
