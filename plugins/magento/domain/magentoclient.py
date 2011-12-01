# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.log import Logger
from twisted.internet.defer import succeed

from stoqlib.database.orm import ForeignKey
from stoqlib.domain.address import Address, CityLocation
from stoqlib.domain.interfaces import IClient, IIndividual
from stoqlib.domain.person import Person
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.validators import validate_cpf

from domain.magentobase import MagentoBaseSyncDown

_ = stoqlib_gettext
log = Logger('plugins.magento.domain.magentoclient')


class MagentoClient(MagentoBaseSyncDown):
    """Class for client synchronization between Stoq and Magento"""

    API_NAME = 'customer'
    API_ID_NAME = 'customer_id'

    (ERROR_CUSTOMER_INVALID_DATA,
     ERROR_CUSTOMER_INVALID_FILTERS,
     ERROR_CUSTOMER_NOT_EXISTS,
     ERROR_CUSTOMER_NOT_DELETED) = range(100, 104)

    (GENDER_MALE,
     GENDER_FEMALE) = range(1, 3)

    client = ForeignKey('PersonAdaptToClient', default=None)

    #
    #  MagentoBaseSyncDown hooks
    #

    def need_create_local(self):
        return not self.client

    def create_local(self, info):
        assert self.need_create_local()

        # Some parts of name maybe will come as None or ''
        name = ' '.join([part for part in (info['firstname'],
                                           info['middlename'],
                                           info['lastname']) if part])
        email = info['email']
        cpf = info['taxvat'] if validate_cpf(info['taxvat']) else None

        self.client = self._get_or_create_client(name, email, cpf)
        person = self.client.person

        # TRANSLATORS: #%d refers to the user's ID on Magento
        notes = [_("Magento user #%s") % info[self.API_ID_NAME]]
        if person.notes:
            notes.append(person.notes)
        person.notes = "\n\n".join(notes)

        return self.update_local(info)

    def update_local(self, info):
        person = self.client.person
        individual = IIndividual(person, None)
        if not individual:
            # Just log if we don't have individual anymore. If we
            # try to fix this here, we will be masking the problem
            # somewhere else.
            log.warning("Unexpected error: Person '%s' is missing "
                        "IIndividual facet" % person)
            return False

        person.email = info['email']
        if info['dob']:
            birth_date = info['dob']
            individual.birth_date = birth_date
        if info['gender']:
            individual.gender = self._get_gender(info['gender'])

        if not individual.cpf and validate_cpf(info['taxvat']):
            # Just update the cpf if we did not have any before
            individual.cpf = info['taxvat']

        # FIXME: This is a workaround to solve the issue pointed on
        #        MagentoAddress's list method. Remove this for when solving it
        for mag_address_id in (info['default_billing'],
                               info['default_shipping']):
            if not mag_address_id:
                # Maybe the user didn't set any addresses yet
                continue
            conn = self.get_connection()
            mag_address = MagentoAddress.selectOneBy(connection=conn,
                                                     config=self.config,
                                                     magento_id=mag_address_id)
            if not mag_address:
                mag_address = MagentoAddress(connection=conn,
                                             config=self.config,
                                             magento_id=mag_address_id,
                                             magento_client=self)
            mag_address.need_sync = True

        return True

    #
    #  Private
    #

    def _get_or_create_client(self, name, email, cpf):
        conn = self.get_connection()

        # Check for existing person using the given email
        person = Person.selectOneBy(connection=conn,
                                    email=email)
        if person:
            if not IClient(person, None):
                person.addFacet(IClient,
                                connection=conn)
            if not IIndividual(person, None):
                person.addFacet(IIndividual,
                                connection=conn,
                                cpf=cpf)
            return IClient(person)

        # Check for existing person using the given cpf
        if cpf:
            individual = Person.iselectOneBy(IIndividual, connection=conn,
                                             cpf=cpf)
            if individual:
                if not IClient(individual.person, None):
                    individual.person.addFacet(IClient,
                                               connection=conn)
                return IClient(individual.person)

        # Create a new one
        person = Person(connection=conn,
                        name=name,
                        email=email)
        person.addFacet(IIndividual, connection=conn,
                        cpf=cpf)
        person.addFacet(IClient, connection=conn)

        return IClient(person)

    def _get_gender(self, mag_gender):
        if mag_gender == self.GENDER_MALE:
            return Person.GENDER_MALE
        if mag_gender == self.GENDER_FEMALE:
            return Person.GENDER_FEMALE

        return None


class MagentoAddress(MagentoBaseSyncDown):
    """Class for address synchronization between Stoq and Magento"""

    API_NAME = 'customer_address'
    API_ID_NAME = 'customer_address_id'

    (ERROR_ADDRESS_INVALID_DATA,
     ERROR_ADDRESS_CUSTOMER_NOT_EXISTS,
     ERROR_ADDRESS_NOT_EXISTS,
     ERROR_ADDRESS_NOT_DELETED) = range(100, 104)

    address = ForeignKey('Address', default=None)
    magento_client = ForeignKey('MagentoClient', default=None)

    #
    #  MagentoBase hooks
    #

    @classmethod
    def list_remote(cls, *args, **kwargs):
        # FIXME: The magento address api doesn't support filters yet. So,
        #        there is no way to optimize the call. For now, we return
        #        an empty list here, so sync will only process objs that
        #        has 'need_sync == True'. The responsible for doing this
        #        in the moment is MagentoClient.
        return succeed([])

    #
    #  MagentoBaseSyncDown hooks
    #

    def need_create_local(self):
        return not self.address

    def create_local(self, info):
        conn = self.get_connection()
        sysparam_ = sysparam(conn)

        city = info['city'] or sysparam_.CITY_SUGGESTED
        state = info['region'] or sysparam_.STATE_SUGGESTED
        country = sysparam_.COUNTRY_SUGGESTED
        city_location = CityLocation.get_or_create(conn, city, state, country)

        person = self.magento_client.client.person
        # FIXME: Is there a way to split the street in a secure way?
        #        On my examples it came as 'Rua Rui Barbosa, 2000\nCentro'
        #        It's because the address there is get by 2 textfields,
        #        but there is no way we can make sure the user filled
        #        those exactly as I did...
        street = info['street'].replace('\n', ' | ')
        postal_code = info['postcode']

        self.address = Address(connection=conn,
                               street=street,
                               postal_code=str(postal_code),
                               person=person,
                               city_location=city_location)

        if info['is_default_billing']:
            # If the address is the default billing one, lets
            # update some client information that is withint it.
            person.phone_number = info['telephone']
            person.fax_number = info['fax']

        return self.update_local(info)

    def update_local(self, info):
        if info['is_default_billing']:
            self._set_main_address()

        return True

    #
    #  Private
    #

    def _set_main_address(self):
        addresses = Address.selectBy(connection=self.get_connection(),
                                     person=self.magento_client.client.person)
        for address in addresses:
            if address == self.address:
                address.is_main_address = True
                continue

            address.is_main_address = False
