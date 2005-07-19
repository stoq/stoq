# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
gui/editors/person_editor.py

    Base classes for person editors
"""

from kiwi.ui.widgets.list import Column
from stoqlib.gui.editors import (BaseEditor, BaseEditorSlave,
                                 BasicWrappingDialog)
from stoqlib.gui.dialogs import run_dialog
from stoqlib.gui.slaves import NoteSlave
from stoqlib.gui.lists import AdditionListSlave, AdditionListDialog

from stoq.domain.person import Address, CityLocation, Liaison, Person
from stoq.domain.base_model import (ModelAdapter, 
                                    InheritableModelAdapter)
from stoq.lib.parameters import get_system_parameter
from stoq.lib.runtime import new_transaction


class AddressAdditionDialog(AdditionListDialog):
    
    def __init__(self, conn, parent, editor_class, columns, 
                 klist_objects, **editor_kwargs):
        title = _('Address List')
        AdditionListDialog.__init__(self, conn, parent, editor_class, columns, 
                                    klist_objects, title, **editor_kwargs)
        self.cancel_button.hide()
    
    def on_delete_items(self, items):
        assert len(items) >= 1
        table = Address
        for item in items:
            table.delete(item.id, connection=self.conn)        


class AddressSlave(BaseEditorSlave):
    title = _('Address Editor')
    gladefile = 'AddressSlave'
    model_type = Address

    address_proxy_widgets = ('street',
                             'number',
                             'complement',
                             'district',
                             'postal_code',
                             'country',
                             'city',
                             'state')
    widgets = address_proxy_widgets + ('checkbutton', )
    
    def __init__(self, parent, conn, person_model, model=None):
        self.parent = parent
        self.person_model = person_model
        BaseEditorSlave.__init__(self, conn, model)
        self.initialize()

    def setup_validation(self):
        self.main_dialog = self.parent.main_dialog
        self.register_validate_function(self.parent.refresh_ok)

    def setup_proxies(self):
        self.address_proxy = self.add_proxy(widgets=self.address_proxy_widgets)

    def initialize(self):
        """ Initialize properly the model (creating a new if it doesn't exist),
the proxies (i.e, the proxy model) and the city location combos. """
        if self.model is None:
            city_location = CityLocation(connection=self.conn)
            is_main_address = not isinstance(self, AddressEditor)
            self.model = Address(person=self.person_model,
                                 is_main_address=is_main_address,
                                 city_location=city_location,
                                 connection=self.conn)
        else:
            # XXX: We always need a copy of city_location object, since this
            # copy will be removed in ensure_address() if the editor is
            # opened for edition and the user changes the data in the combos
            self.model.city_location = self.model.city_location.clone()

        self.setup_combos()
        self.address_proxy.new_model(self.model)

    def update_proxies(self, address_obj):
        assert(address_obj)
        self.address_proxy.new_model(address_obj)

    def setup_combos(self):
        for combo in (self.city, self.state, self.country):
            combo.clear()

        city_location_list = CityLocation.select(connection=self.conn)
        conn = self.conn
        sparam = get_system_parameter(conn)
        cities = [sparam.CITY_SUGGESTED]
        countries = [sparam.COUNTRY_SUGGESTED]
        states = sparam.CITY_LOCATION_STATES

        for cityloc in city_location_list:
            if cityloc.city and cityloc.city not in cities:
                cities.append(cityloc.city)
                
            if cityloc.country and cityloc.country not in countries:
                countries.append(cityloc.country)

            if cityloc.state and cityloc.state not in states:
                states.append(cityloc.state)

        self.city.prefill(cities, sort=True)
        self.country.prefill(countries, sort=True)
        self.state.prefill(states, sort=True)



    #
    # Hook methods
    #



    def validate_confirm(self):
        """ If there is a street filled the user need to set the city, state 
and country. """
        if self.main_dialog is None:
            assert self.parent.main_dialog
            self.main_dialog = self.parent.main_dialog
        
        cityloc = self.model.city_location
        if self.model.street and not \
           (cityloc.city and cityloc.country and cityloc.state):
            msg = _('You must fill the City, State and Country fields.')
            self.main_dialog.alert(msg)
            return False

        return True

    def ensure_address(self):
        """ Check if we already have the CityLocation specified by the user,
if so we check if they are the same, if so, do nothing; otherwise, get the 
city location stored and delete the current. """

        cityloc = self.model.city_location

        #
        # Ensure that the city_location doesn't exist in the table.
        #
        query = ("city = '%s' AND state = '%s' AND country = '%s'" % 
                 (cityloc.city, cityloc.state, cityloc.country))
        conn = new_transaction()
        rv = CityLocation.select(query, connection=conn)
        conn.close()

        if rv.count():
            msg = ("You should get just one city_location instance. "
                   "Probably you have a database inconsistency.")
            assert rv.count() == 1, msg

            if cityloc.id != rv[0].id:
                obj = CityLocation.get(rv[0].id)
                self.model.city_location = obj
                CityLocation.delete(cityloc.id, connection=self.conn)

        main_address = self.person_model.get_main_address()
        if (self.checkbutton.get_active() and 
            self.model is not main_address):
            self.model.is_main_address = 1
            main_address.is_main_address = 0
         
    def on_confirm(self):
        # Hook method called by parent window
        self.ensure_address()


    def on_confirm(self):
        # Hook method called by parent window
        self.ensure_address()
        return self.model        


class AddressEditor(AddressSlave):
    title = _('Address Editor')
    model_type = Address
    header = ''
    size = ()
    
    def __init__(self, conn, person_model, model=None):
        AddressSlave.__init__(self, self, conn, person_model, model)
        self.main_dialog = BasicWrappingDialog(self, self.title, self.header, 
                                               self.size)
        self.main_dialog.enable_notices()
        # This a subclass of BaseEditorSlave which doesn't have a
        # main_dialog attribute by default. Here we added this attribute and
        # also need to call explicitly register_validate_function to
        # control ok button sensitivity properly. 
        #XXX Bug 2030 will improve this part.
        self.register_validate_function(self.refresh_ok)
    
    def initialize(self):
        AddressSlave.initialize(self)

        self.checkbutton.set_property('visible', True)
        main = (bool(self.person_model.addresses) and 
                self.model.is_main_address)
        self.checkbutton.set_active(main)

    def refresh_ok(self, validation_value):
        self.main_dialog.ok_button.set_sensitive(validation_value)


class ContactEditor(BaseEditor):
    gladefile = 'ContactEditor'
    model_type = Liaison
    widgets = ('name', 'phone_number')

    title = _('Liaison Editor')
    
    def __init__(self, conn, person_obj, model=None):
        if not model:
            model = Liaison(person=person_obj, connection=conn)
        
        BaseEditor.__init__(self, conn, model)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.widgets)

    def validate_confirm(self):
        # Hook method called by main_dialog.confirm
        msg = ('A proxy attribute should be already set at this point.')
        assert self.model is not None, msg
        
        if (self.model.name == '' or 
            self.model.phone_number == ''):
            msg = ('You must supply both name and phone number for a '
                   'contact.')
            self.main_dialog.error(msg)
            return False
        return True
    

class PersonEditor(BaseEditor):
    title = _('Person Editor')
    model_type = Person
    gladefile = 'PersonEditor'

    proxy_widgets = ('name',
                     'phone_number',
                     'mobile_number',
                     'fax_number',
                     'email')

    widgets =       ('notebook1',                  
                     'person_id_holder',
                     'main_address_holder',
                     'person_status_holder',
                     'person_details_holder',
                     'contact_list_holder',
                     'custom_holder',
                     'note_holder',
                     'address_button') + proxy_widgets
    
    def __init__(self, conn, model=None):
        self.person_model = model
        model_types = (ModelAdapter, InheritableModelAdapter)

        if model and isinstance(model, model_types):
            self.person_model = model.get_adapted()
        elif not model:
            self.person_model = Person(name='', connection=conn)

        BaseEditor.__init__(self, conn, model)
        self.main_dialog.enable_notices()
        self.main_address_slave.setup_validation()

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.person_model, self.proxy_widgets)

    def setup_slaves(self):
        contact_columns = [Column('name', 'Name', data_type=str),
                           Column('phone_number', 'Phone Number', 
                                  data_type=str)]

        # Address Slave
        main_address = self.person_model.get_main_address()

        self.main_address_slave = AddressSlave(self, self.conn,
                                               self.person_model, main_address)
        self.attach_slave('main_address_holder', self.main_address_slave)

        liaisons = self.person_model.liaisons
        slave = AdditionListSlave(self.conn, self, ContactEditor, 
                                  contact_columns, klist_objects=liaisons,
                                  person_obj=self.person_model)
        self.attach_slave('contact_list_holder', slave)
        
        slave = NoteSlave(self.conn, self.person_model)
        self.attach_slave('note_holder', slave)
    
    def on_address_button__clicked(self, *args):
        address_columns = [Column('street', title=_('Street'), data_type=str), 
                           Column('number', title=_('Number'), data_type=int),
                           Column('complement', title=_('Complement'), 
                                  data_type=str, visible=False), 
                           Column('city_location.city', title=_('City'),
                                  data_type=str), 
                           Column('city_location.state', title=_('State'), 
                                  data_type=str), 
                           Column('city_location.country', 
                                  title=_('Country'),
                                  data_type=str, visible=False), 
                           Column('postal_code', title=_('Postal Code'), 
                                  data_type=str, visible=False)]

        addresses = self.person_model.addresses
        main_address = self.person_model.get_main_address()
        addresses = [a for a in addresses if a is not main_address]

        run_dialog(AddressAdditionDialog, self.main_dialog, self.conn, self, 
                   editor_class=AddressEditor, columns=address_columns, 
                   klist_objects=addresses, person_model=self.person_model)

        # Check if we change the main address and update the proxy associated
        # to main_address slave
        new_main_address = self.person_model.get_main_address()

        if new_main_address is not main_address:
            self.main_address_slave.setup_combos()
            self.main_address_slave.update_proxies(new_main_address)



    #
    # Hooks
    #



    def on_delete_items(self, items):
        # Hook called by Liaison AdditionListSlave
        assert len(items) >= 1
        table = Liaison
        for item in items:
            table.delete(item.id, connection=self.conn)

    def on_add_item(self, *args):
        """Hook called by Liaison AdditionListSlave"""

    def on_edit_item(self, *args):
        """Hook called by Liaison AdditionListSlave"""

    def validate_confirm(self):
        return self.main_address_slave.validate_confirm()
  
    def on_confirm(self):
        self.main_address_slave.ensure_address()
        return self.person_model


