# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2012 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
"""Person domain classes

The Person domain classes in Stoqlib are special since the :obj:`Person`
class is small and additional functionality is provided through
facets.

There are currently the following person facets available:

  * |branch| - a physical location within a company
  * |client| - when buying something from a branch
  * |company| - a company, tax entitity
  * |employee| - works for a branch
  * |individual| - physical person
  * |loginuser| - can login and use the system
  * :obj:`SalesPerson` - can sell to clients
  * |supplier| - provides product and services to a branch
  * |transporter| - transports deliveries to/from a branch

To create a new person, just issue the following::

    >>> from stoqlib.database.runtime import new_store
    >>> store = new_store()

    >>> person = Person(name=u"A new person", store=store)

Then to add a client, you can will do:

    >>> client = Client(person=person, store=store)

"""

# pylint: enable=E1101

import collections
import hashlib
import operator

from kiwi.currency import currency
from kiwi.datatypes import converter
from storm.expr import (And, Coalesce, Eq, Join, LeftJoin, Or, Update, Select,
                        Alias, Sum)
from storm.info import ClassAlias
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.expr import (Age, Case, Concat, Date, DateTrunc, Interval,
                                   Field, NotIn, StoqNormalizeString)
from stoqlib.database.properties import (BoolCol, DateTimeCol,
                                         IntCol, PercentCol,
                                         PriceCol, EnumCol,
                                         UnicodeCol, IdCol)
from stoqlib.database.viewable import Viewable
from stoqlib.database.runtime import get_current_station, get_current_branch
from stoqlib.domain.address import Address
from stoqlib.domain.base import Domain
from stoqlib.domain.event import Event
from stoqlib.domain.interfaces import IDescribable, IActive
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.profile import UserProfile
from stoqlib.enums import LatePaymentPolicy
from stoqlib.exceptions import DatabaseInconsistency, LoginError, SellError
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.formatters import raw_phone_number, format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import locale_sorted, stoqlib_gettext

_ = stoqlib_gettext


#
# Base Domain Classes
#


@implementer(IDescribable)
class EmployeeRole(Domain):
    """Base class to store the |employee| roles."""

    __storm_table__ = 'employee_role'

    name = UnicodeCol()

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def has_other_role(self, name):
        """Check if there is another role with the same name

        :param name: name of the role to check
        :returns: ``True`` if it exists, otherwise ``False``
        """
        return self.check_unique_value_exists(
            EmployeeRole.name, name, case_sensitive=False)


# WorkPermitData, MilitaryData, and VoterData are Brazil-specific information.
class WorkPermitData(Domain):
    """Work permit data for an |employee|.

    .. note:: This is Brazil-specific information.
    """

    __storm_table__ = 'work_permit_data'

    number = UnicodeCol(default=None)
    series_number = UnicodeCol(default=None)
    #: number of PIS ("Programa de Integracao Social")
    pis_number = UnicodeCol(default=None)
    #: bank PIS ("Programa de Integracao Social")
    pis_bank = UnicodeCol(default=None)
    #: registry date of PIS ("Programa de Integracao Social")
    pis_registry_date = DateTimeCol(default=None)


class MilitaryData(Domain):
    """ Military data for an |employee|.

    .. note:: This is Brazil-specific information.

    """

    __storm_table__ = 'military_data'

    number = UnicodeCol(default=None)
    series_number = UnicodeCol(default=None)
    category = UnicodeCol(default=None)


class VoterData(Domain):
    """Voter data for an |employee|.

    .. note:: This is Brazil-specific information.
    """

    __storm_table__ = 'voter_data'

    number = UnicodeCol(default=None)
    section = UnicodeCol(default=None)
    zone = UnicodeCol(default=None)


@implementer(IDescribable)
class ContactInfo(Domain):
    """Class to store the person's contact information.
    This can be used to store:

    * phone numbers (land lines and mobile)
    * email addresses
    * web sites (corporate, home, Facebook, Google Plus)
    * IM contact information
    * contact of other people inside an organization"""

    __storm_table__ = 'contact_info'

    #: describes what the contact information is, e.g. Home Phone Number
    description = UnicodeCol(default=u'')

    #: the contact information itself, e.g. 1234-5678, user@example.com, ...
    contact_info = UnicodeCol(default=u'')

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #
    # IDescribable
    #

    def get_description(self):
        return self.description


class CreditCheckHistory(Domain):
    """Client credit check history

    This stores credit information about a |client|.

    From time to time, a store may contact some 'credit protection agency' that
    will inform the status of a certain client, for instance, if the client has
    active debt with other companies.
    """

    __storm_table__ = 'credit_check_history'

    #: if a client has debt
    STATUS_INCLUDED = u'included'

    #: if a client does not have debt
    STATUS_NOT_INCLUDED = u'not-included'

    statuses = {STATUS_INCLUDED: _(u'Included'),
                STATUS_NOT_INCLUDED: _(u'Not included')}

    #: when this check was created
    creation_date = DateTimeCol(default_factory=localnow)

    #: when the check was made
    check_date = DateTimeCol()

    # FIXME: Change identifier to another name, to avoid confusions
    # with IdentifierCol used elsewhere
    #: an unique identifier created by the agency
    identifier = UnicodeCol()

    #: the client status given the options above
    status = EnumCol(allow_none=False, default=STATUS_INCLUDED)

    #: notes about the credit check history created by the user
    notes = UnicodeCol()

    client_id = IdCol()

    #: the |client|
    client = Reference(client_id, 'Client.id')

    user_id = IdCol()

    #: the `user` that created this entry
    user = Reference(user_id, 'LoginUser.id')


@implementer(IDescribable)
class Calls(Domain):
    """Person's calls information.

    Calls are information associated to a |person| (|client|, |supplier|,
    |employee|, etc) that can be financial problems registries,
    collection letters information, some problems with a product
    delivered, etc.
    """

    __storm_table__ = 'calls'

    date = DateTimeCol()
    description = UnicodeCol()
    message = UnicodeCol()

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    attendant_id = IdCol()

    attendant = Reference(attendant_id, 'LoginUser.id')

    #
    # IDescribable
    #

    def get_description(self):
        return self.description


def _validate_number(person, attr, number):
    if number is None:
        number = u''
    return raw_phone_number(number)


# A Person can actually be thought of as a "Contactable", to use
# the same terminology as Storable/Sellable.
class Person(Domain):
    """A Person, an entity that can be contacted (via phone, email).
    It usually has an |address|.
    """

    __storm_table__ = 'person'

    # FIXME: These two are internal to person template and should be
    # moved there.
    (ROLE_INDIVIDUAL,
     ROLE_COMPANY) = range(2)

    #: name of the person, depending on the facets, it can either
    #: be something like "John Doe" or "Microsoft Corporation"
    name = UnicodeCol()

    #: phone number for this person
    phone_number = UnicodeCol(default=u'', validator=_validate_number)

    #: cell/mobile number for this person
    mobile_number = UnicodeCol(default=u'', validator=_validate_number)

    #: fax number for this person
    fax_number = UnicodeCol(default=u'', validator=_validate_number)

    #: email address
    email = UnicodeCol(default=u'')

    #: notes about the person
    notes = UnicodeCol(default=u'')

    #: all `contact information <ContactInfo>` related to this person
    contact_infos = ReferenceSet('id', 'ContactInfo.person_id')

    #: list of |addresses|
    addresses = ReferenceSet('id', 'Address.person_id')

    #: all `calls <Calls>` made to this person
    calls = ReferenceSet('id', 'Calls.person_id')

    #: the |branch| facet for this person
    branch = Reference('id', 'Branch.person_id', on_remote=True)

    #: the |client| facet for this person
    client = Reference('id', 'Client.person_id', on_remote=True)

    #: the |company| facet for this person
    company = Reference('id', 'Company.person_id', on_remote=True)

    #: |employee| facet for this person
    employee = Reference('id', 'Employee.person_id', on_remote=True)

    #: |individual| for this person
    individual = Reference('id', 'Individual.person_id', on_remote=True)

    #: |loginuser| facet for this person
    login_user = Reference('id', 'LoginUser.person_id', on_remote=True)

    #: the :obj:`sales person <SalesPerson>` facet for this person
    sales_person = Reference('id', 'SalesPerson.person_id', on_remote=True)

    #: the |supplier| facet for this person
    supplier = Reference('id', 'Supplier.person_id', on_remote=True)

    #: the |transporter| facet for this person
    transporter = Reference('id', 'Transporter.person_id', on_remote=True)

    #: The id of the person this person has been merged into. When a person is
    #: merged into another one. All references to that person (and its facets)
    #: are updated to the other person.
    merged_with_id = IdCol()

    @property
    def address(self):
        """The |address| for this person
        """
        return self.get_main_address()

    #
    # Classmethods
    #

    @classmethod
    def get_by_document(cls, store, document):
        """
        Returns a |person| given a specific document.

        :param store: a database store
        :param document: a document can be a cpf from a |individual|
        or a cnpj from a |company| (Brazil standard)
        :returns: |person|
        """
        query = Or(Individual.cpf == document,
                   Company.cnpj == document)

        tables = [Person,
                  LeftJoin(Individual, Person.id == Individual.person_id),
                  LeftJoin(Company, Person.id == Company.person_id)]
        return store.using(*tables).find(Person, query).one()

    #
    # Acessors
    #

    def get_main_address(self):
        """The primary |address| for this person. It is normally
        set when you register the client for the first time.
        """
        return self.store.find(Address,
                               person_id=self.id,
                               is_main_address=True).one()

    def get_total_addresses(self):
        """The total number of |addresses| for this person.

        :returns: the number of |addresses|
        """
        return self.store.find(Address, person_id=self.id).count()

    def get_address_string(self):
        """The primary |address| for this person formatted as a string.

        :returns: the |address|
        """
        address = self.get_main_address()
        if not address:
            return u''
        return address.get_address_string()

    def get_phone_number_number(self):
        """Returns the phone number without any non-numeric characters

        :returns: the phone number as a number
        """
        if not self.phone_number:
            return 0
        return int(''.join([c for c in self.phone_number
                            if c in u'1234567890']))

    def get_fax_number_number(self):
        """Returns the fax number without any non-numeric characters

        :returns: the fax number as a number
        """
        if not self.fax_number:
            return 0
        return int(''.join([c for c in self.fax_number
                            if c in u'1234567890']))

    def get_formatted_phone_number(self):
        """
        :returns: a dash-separated phone number or an empty string
        """
        if self.phone_number:
            return format_phone_number(self.phone_number)
        return u""

    def get_formatted_fax_number(self):
        """
        :returns: a dash-separated fax number or an empty string
        """
        if self.fax_number:
            return format_phone_number(self.fax_number)
        return u""

    def get_formatted_mobile_number(self):
        """
        :returns: a dash-separated fax number or an empty string
        """
        if self.mobile_number:
            return format_phone_number(self.mobile_number)
        return u""

    @classmethod
    def get_items(cls, store, query):
        """
        Return a list of items (name, id)

        :param store: a store
        :returns: the items
        """
        join = LeftJoin(Company, And(Company.person_id == Person.id, query))
        items = store.using(Person, join).find((Coalesce(Concat(Company.fancy_name, u" (",
                                               Person.name, u")"), Person.name), cls.id))

        return locale_sorted(items, key=operator.itemgetter(0))

    #
    # Public API
    #

    def get_cnpj_or_cpf(self):
        """Returns this person cnpf or cpf

        If the person is a company, return its cnpj, otherwise, return its
        cpf.
        """
        if self.company:
            return self.company.cnpj
        elif self.individual:
            return self.individual.cpf

    def has_individual_or_company_facets(self):
        return self.individual or self.company

    def merge_facet(self, this_facet, other_facet):
        if not other_facet:
            return

        if this_facet is not None:
            # if the other person has the facet and so do we, se should: Fix all
            # objects that reference that facet and make them reference this
            # facet; and remove that facet.
            this_facet.merge_with(other_facet)
        else:
            # If the other person has the facet but we dont, we just need
            # to fix the reference of that facet.
            other_facet.person = self

    def merge_with(self, other, copy_empty_values=True):
        """Merges this person with other objects

        This will fix all references that point to the other person, and make
        them point to this person.
        """
        skip = set([('person', 'merged_with_id')])
        facets = ['branch', 'individual', 'company', 'client', 'transporter',
                  'supplier', 'sales_person', 'login_user', 'employee']
        for facet in facets:
            skip.add((facet, 'person_id'))
            this_facet = getattr(self, facet)
            other_facet = getattr(other, facet)
            self.merge_facet(this_facet, other_facet)

        skip.add(('address', 'person_id'))
        if copy_empty_values:
            if other.notes:
                self.notes += '\n' + other.notes

            if self.address and other.address:
                self.address.copy_empty_values(other.address)

        super(Person, self).merge_with(other, skip, copy_empty_values)
        other.merged_with_id = self.id


@implementer(IActive)
@implementer(IDescribable)
class Individual(Domain):
    """Being or characteristic of a single person, concerning one
    person exclusively

    """

    __storm_table__ = 'individual'

    STATUS_SINGLE = u'single'
    STATUS_MARRIED = u'married'
    STATUS_DIVORCED = u'divorced'
    STATUS_WIDOWED = u'widowed'
    # FIXME: Change to 'separated' after fix this typo in database.
    STATUS_SEPARATED = u'separeted'
    STATUS_COHABITATION = u'cohabitation'

    marital_statuses = collections.OrderedDict([
        (STATUS_SINGLE, _(u"Single")),
        (STATUS_MARRIED, _(u"Married")),
        (STATUS_DIVORCED, _(u"Divorced")),
        (STATUS_WIDOWED, _(u"Widowed")),
        (STATUS_SEPARATED, _(u'Separated')),
        (STATUS_COHABITATION, _(u'Cohabitation')),
    ])

    GENDER_MALE = u'male'
    GENDER_FEMALE = u'female'

    genders = {GENDER_MALE: _(u'Male'),
               GENDER_FEMALE: _(u'Female')}

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    # FIXME: rename to "document"
    #: the national document used to identify this person.
    cpf = UnicodeCol(default=u'')

    #: A Brazilian government register which identify an individual
    rg_number = UnicodeCol(default=u'')

    #: when this individual was born
    birth_date = DateTimeCol(default=None)

    #: current job
    occupation = UnicodeCol(default=u'')

    #: martial status, single, married, widow etc
    marital_status = EnumCol(allow_none=False, default=STATUS_SINGLE)

    #: Name of this individuals father
    father_name = UnicodeCol(default=u'')

    #: Name of this individuals mother
    mother_name = UnicodeCol(default=u'')

    #: When the rg number was issued
    rg_expedition_date = DateTimeCol(default=None)

    #: Where the rg number was issued
    rg_expedition_local = UnicodeCol(default=u'')

    #: male or female
    gender = EnumCol(allow_none=False, default=GENDER_MALE)

    #: the name of the spouse individual's partner in marriage
    spouse_name = UnicodeCol(default=u'')

    birth_location_id = IntCol(default=None)

    #: the |location| where individual was born
    birth_location = Reference(birth_location_id, 'CityLocation.id')

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This individual is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This individual is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def merge_with(self, other, copy_empty_values=True):
        skip = None
        super(Individual, self).merge_with(other, skip, copy_empty_values)
        # If we copied the value from the other object, we also need to reset
        # it, so that there are no duplicate documents in the database
        if copy_empty_values:
            other.cpf = u''

    def get_marital_statuses(self):
        return [(self.marital_statuses[i], i)
                for i in self.marital_statuses.keys()]

    def get_cpf_number(self):
        """Returns the cpf number without any non-numeric characters

        :returns: the cpf number as a number
        """
        if not self.cpf:
            return 0
        return int(''.join([c for c in self.cpf if c in '1234567890']))

    def check_cpf_exists(self, cpf):
        """Returns ``True`` if we already have a Individual with the given CPF
        in the database.
        """
        return self.check_unique_value_exists(Individual.cpf, cpf)

    @classmethod
    def get_birthday_query(cls, start, end=None):
        """
        Get a database query suitable to use in a SearchColumn.search_func
        callback. This can either be searching for a birthday in a date or
        an interval of dates.

        :param start: start date
        :param end: for intervals, an end date, use ``None`` for single days
        :returns: the database query
        """
        start_year = DateTrunc(u'year', Date(start))
        age_in_year = Age(cls.birth_date, DateTrunc(u'year', cls.birth_date))
        next_birthday = (
            start_year + age_in_year +
            Case(condition=age_in_year < Age(Date(start), start_year),
                 result=Interval(u"1 year"),
                 else_=Interval(u"0 year"))
        )

        if end is None:
            return next_birthday == Date(start)
        else:
            return And(next_birthday >= Date(start),
                       next_birthday <= Date(end))


@implementer(IActive)
@implementer(IDescribable)
class Company(Domain):
    """An institution created to conduct business
    """

    __storm_table__ = 'company'

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    # FIXME: rename to document
    #: a number identifing the company
    cnpj = UnicodeCol(default=u'')

    #: Doing business as (dba) name for this company, a secondary, non-legal
    #: name of the company.
    fancy_name = UnicodeCol(default=u'')

    #: Brazilian register number associated with a certain state
    state_registry = UnicodeCol(default=u'')

    #: Brazilian register number associated with a certain city
    city_registry = UnicodeCol(default=u'')

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This company is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This company is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def merge_with(self, other, copy_empty_values=True):
        skip = None
        super(Company, self).merge_with(other, skip, copy_empty_values)
        # If we copied the value from the other object, we also need to reset
        # it, so that there are no duplicate documents in the database
        if copy_empty_values:
            other.cnpj = u''

    def get_cnpj_number(self):
        """Returns the cnpj number without any non-numeric characters

        :returns: the cnpj number as a number
        """
        if not self.cnpj:
            return 0

        # FIXME: We should return cnpj as strings, since it can begin with 0
        num = u''.join([c for c in self.cnpj if c in u'1234567890'])
        if num:
            return int(num)
        return 0

    def get_state_registry_number(self):
        """Returns the state registry number without any non-numeric characters

        :returns: the state registry number as a number or zero if there is
          no state registry.
        """
        if not self.state_registry:
            return 0

        numbers = u''.join([c for c in self.state_registry
                            if c in u'1234567890'])
        return int(numbers or 0)

    def check_cnpj_exists(self, cnpj):
        """Returns ``True`` if we already have a Company with the given CNPJ
        in the database.
        """
        return self.check_unique_value_exists(Company.cnpj, cnpj)


@implementer(IDescribable)
class ClientCategory(Domain):
    """I am a client category.
    """

    __storm_table__ = 'client_category'

    #: name of the category
    name = UnicodeCol()

    #: max discount for clients of this category
    max_discount = PercentCol(default=0)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def can_remove(self):
        """ Check if the client category is used in some product."""
        return super(ClientCategory, self).can_remove(
            skip=[('client', 'category_id')])

    def remove(self):
        """Remove this client category from the database."""
        self.store.execute(Update(
            {Client.category_id: None}, Client.category_id == self.id, Client))

        self.store.remove(self)


@implementer(IActive)
@implementer(IDescribable)
class Client(Domain):
    """An individual or a company who pays for goods or services

    """

    __storm_table__ = 'client'

    STATUS_SOLVENT = u'solvent'
    STATUS_INDEBTED = u'indebt'
    STATUS_INSOLVENT = u'insolvent'
    STATUS_INACTIVE = u'inactive'

    statuses = collections.OrderedDict([
        (STATUS_SOLVENT, _(u'Solvent')),
        (STATUS_INDEBTED, _(u'Indebted')),
        (STATUS_INSOLVENT, _(u'Insolvent')),
        (STATUS_INACTIVE, _(u'Inactive')),
    ])

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #: ok, indebted, insolvent, inactive
    status = EnumCol(allow_none=False, default=STATUS_SOLVENT)

    #: How many days is this client indebted
    days_late = IntCol(default=0)

    #: How much the user can spend on store credit, this is not
    #: related to credit given when returning a sale. It's basically
    #: how much this client can buy before having to pay.
    credit_limit = PriceCol(default=0)

    category_id = IdCol(default=None)

    #: the :obj:`client category <ClientCategory>` for this client
    category = Reference(category_id, 'ClientCategory.id')

    #: client salary
    _salary = PriceCol(u'salary', default=0)

    #: all the sales to this client
    sales = ReferenceSet('id', 'Sale.client_id')

    #
    # IActive
    #

    def get_status_string(self):
        if not self.status in self.statuses:
            raise DatabaseInconsistency('Invalid status for client, '
                                        'got %d' % self.status)
        return self.statuses[self.status]

    def inactivate(self):
        if self.status == Client.STATUS_INACTIVE:
            raise AssertionError('This client is already inactive')
        self.status = self.STATUS_INACTIVE

    def activate(self):
        if self.status == Client.STATUS_SOLVENT:
            raise AssertionError('This client is already active')
        self.status = self.STATUS_SOLVENT

    @property
    def is_active(self):
        return self.status == self.STATUS_SOLVENT

    @is_active.setter
    def is_active(self, value):
        if value:
            self.activate()
        else:
            self.inactivate()

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_active_items(cls, store):
        """
        Return a list of active items (name, id)

        :param store: a store
        :returns: the items
        """
        join1 = LeftJoin(Person, Person.id == Client.person_id)
        join2 = LeftJoin(Company, Company.person_id == Person.id)
        items = store.using(Client, join1, join2).find((
            Coalesce(Concat(Company.fancy_name, u" (", Person.name, u")"), Person.name),
            cls.id),
            And(cls.status != cls.STATUS_INACTIVE))
        return locale_sorted(items, key=operator.itemgetter(0))

    def get_name(self):
        """Name of the client
        """
        return self.person.name

    @classmethod
    def get_active_clients(cls, store):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return store.find(cls, cls.status != cls.STATUS_INACTIVE)

    @classmethod
    def update_credit_limit(cls, percent, store):
        """Updates clients credit limit acordingly to the new percent informed.

        This perecentage is aplied to the client salary to calculate
        the credit limit.

        Only clients with an informed salary will have the credit limit
        updated.

        :param percent: The percentage value that will be used to calculate
          the new credit limit.
        """
        if percent == 0:
            return

        vals = {Client.credit_limit: Client._salary * percent / 100}
        clause = Client._salary > 0
        # XXX This will update the table, but storm wont reload the data. Maybe
        # we should invalidate all clients in cache
        store.execute(Update(vals, clause, Client))

    def get_client_sales(self):
        """Returns a list of :obj:`sale views <stoqlib.domain.sale.SaleView>`
        tied with the current client
        """
        from stoqlib.domain.sale import SaleView
        return self.store.find(SaleView,
                               SaleView.client_id == self.id).order_by(SaleView.open_date)

    def get_client_returned_sales(self):
        """Returns a list of :obj:`returned sales <stoqlib.domain.sale.ReturnedSaleView>`
        tied with the current client
        """
        from stoqlib.domain.sale import ReturnedSaleView
        query = And(ReturnedSaleView.client_id == self.id,
                    Eq(ReturnedSaleView.returned_item.parent_item_id, None))
        returned_sale_view = self.store.find(ReturnedSaleView, query)
        return returned_sale_view.order_by(ReturnedSaleView.return_date)

    def get_client_services(self):
        """Returns a list of sold
        :obj:`service views stoqlib.domain.sale.SoldServicesView>` with
        services consumed by this client
        """
        from stoqlib.domain.sale import SoldServicesView

        return self.store.find(SoldServicesView,
                               client_id=self.id).order_by(SoldServicesView.estimated_fix_date)

    def get_client_work_orders(self):
        """Returns the :class:'stoqlib.domain.WorkOrderView'  associated with a client
        :returns: a sequence of :class:'stoqlib.domain.WorkOrderView'
        """
        from stoqlib.domain.workorder import WorkOrderView
        return self.store.find(WorkOrderView,
                               WorkOrderView.client.id == self.id)

    def get_client_products(self, with_children=True):
        """Returns a list of products from SoldProductsView with products
        sold to the client
        """
        from stoqlib.domain.sale import SoldProductsView
        query = SoldProductsView.client_id == self.id
        if not with_children:
            query = And(query,
                        Eq(SoldProductsView.sale_item.parent_item_id, None))
        return self.store.find(SoldProductsView, query)

    def get_client_payments(self):
        """Returns a list of payment from InPaymentView with client's payments
        """
        from stoqlib.domain.payment.views import InPaymentView
        return self.store.find(InPaymentView,
                               person_id=self.person_id).order_by(InPaymentView.due_date)

    def get_last_purchase_date(self):
        """Fetch the date of the last purchased item by this client.
        None is returned if there are no sales yet made by the client

        :returns: the date of the last purchased item
        """
        from stoqlib.domain.sale import Sale
        max_date = self.get_client_sales().max(Sale.open_date)
        if max_date:
            return max_date.date()

    @property
    def remaining_store_credit(self):
        from stoqlib.domain.payment.views import InPaymentView
        status_query = Or(InPaymentView.status == Payment.STATUS_PENDING,
                          InPaymentView.status == Payment.STATUS_CONFIRMED)
        query = And(InPaymentView.person_id == self.person.id,
                    status_query,
                    InPaymentView.method_name == u'store_credit')

        debit = self.store.find(InPaymentView, query).sum(InPaymentView.value) or currency('0.0')
        return currency(self.credit_limit - debit)

    def get_credit_transactions(self):
        """Returns all credit payments (in and out) associated  with a client's
        credit account.

        :returns: a list of Settables representing payments.
        """
        person = self.store.fetch(self.person)

        payments = self.store.find(
            Payment,
            And(
                # Joins only paid payments.
                Payment.status == Payment.STATUS_PAID,

                # Joins only payments for this client.
                Payment.group_id == PaymentGroup.id,
                PaymentGroup.payer_id == person.id,

                # Joins only credit payments.
                Payment.method_id == PaymentMethod.id,
                PaymentMethod.method_name == u'credit',
            )
        )

        return payments

    @property
    def credit_account_balance(self):
        """Returns a client's credit balance.

        :returns: The client's credit balance."""
        transactions = self.get_credit_transactions()

        balance = 0
        for payment in transactions:
            if payment.payment_type == payment.TYPE_OUT:
                balance += payment.paid_value
            else:
                balance -= payment.paid_value

        return currency(balance)

    @property
    def salary(self):
        return self._salary

    @salary.setter
    def salary(self, value):
        assert value >= 0

        self._salary = value

        salary_percentage = sysparam.get_decimal('CREDIT_LIMIT_SALARY_PERCENT')

        if salary_percentage > 0:
            self.credit_limit = value * salary_percentage / 100

    def can_purchase(self, method, total_amount):
        """This method checks the following to see if the client can
        purchase::

            - The parameter LATE_PAYMENTS_POLICY,
            - The payment method to be used,
            - The total amount of the |payment|,
            - The :obj:`.remaining_store_credit` of this client, when necessary.

        :param method: an |paymentmethod|.
        :param total_amount: the value of the |payment| that should be created
          for this client.
        :returns: ``True`` if user is allowed. Raises an SellError if user is not
          allowed to purchase.
        """
        from stoqlib.domain.payment.views import InPaymentView

        if method.method_name in [u'store_credit', u'credit']:
            if method.method_name == u'store_credit':
                credit_left = self.remaining_store_credit
            else:
                credit_left = self.credit_account_balance

            if credit_left < total_amount:
                raise SellError(_(u'The available credit for this client (%s) '
                                  u'is not enough.') % (
                                converter.as_string(currency, credit_left)))

        # Client does not have late payments
        if not InPaymentView.has_late_payments(self.store,
                                               self.person):
            return True

        param = sysparam.get_int('LATE_PAYMENTS_POLICY')
        if param == LatePaymentPolicy.ALLOW_SALES:
            return True
        elif param == LatePaymentPolicy.DISALLOW_SALES:
            raise SellError(_(u'It is not possible to sell for clients with '
                              u'late payments.'))
        elif (param == LatePaymentPolicy.DISALLOW_STORE_CREDIT
              and method.method_name == u'store_credit'):
            raise SellError(_(u'It is not possible to sell with store credit '
                              u'for clients with late payments.'))

        return True


@implementer(IActive)
@implementer(IDescribable)
class Supplier(Domain):
    """A company or an individual that produces, provides, or furnishes
    an item or service

    """

    __storm_table__ = 'supplier'

    STATUS_ACTIVE = u'active'
    STATUS_INACTIVE = u'inactive'
    STATUS_BLOCKED = u'blocked'

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive'),
                STATUS_BLOCKED: _(u'Blocked')}

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #: active/inactive/blocked
    status = EnumCol(allow_none=False, default=STATUS_ACTIVE)

    #: A short description telling which products this supplier produces
    product_desc = UnicodeCol(default=u'')

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This supplier is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This supplier is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def merge_with(self, other, copy_empty_values=True):
        from stoqlib.domain.product import ProductSupplierInfo
        # product_supplier_info needs special treatment, since there is a unique
        # with the supplier_id
        skip = set([('product_supplier_info', 'supplier_id')])
        subselect = Select(columns=[ProductSupplierInfo.product_id],
                           tables=[ProductSupplierInfo],
                           where=(ProductSupplierInfo.supplier_id == self.id))
        clause = And(ProductSupplierInfo.supplier_id == other.id,
                     NotIn(ProductSupplierInfo.product_id, subselect))
        self.store.execute(Update({ProductSupplierInfo.supplier_id: self.id},
                                  clause, ProductSupplierInfo))

        super(Supplier, self).merge_with(other, skip, copy_empty_values)

    def get_name(self):
        """
        :returns: the supplier's name
        """
        return self.person.name

    @classmethod
    def get_active_suppliers(cls, store):
        query = And(cls.status == cls.STATUS_ACTIVE,
                    cls.person_id == Person.id)
        return store.find(cls, query).order_by(Person.name)

    @classmethod
    def get_active_items(cls, store):
        """
        Return a list of active items (name, id)

        :param store: a store
        :returns: the items
        """

        join1 = LeftJoin(Person, Person.id == cls.person_id)
        join2 = LeftJoin(Company, Company.person_id == Person.id)
        items = store.using(cls, join1, join2).find((
            Coalesce(Concat(Company.fancy_name, u" (", Person.name, u")"), Person.name),
            cls.id),
            And(cls.status == cls.STATUS_ACTIVE))
        return locale_sorted(items, key=operator.itemgetter(0))

    def get_supplier_purchases(self):
        """
        Gets a list of PurchaseOrderViews representing all purchases done from
        this supplier.
        :returns: a list of PurchaseOrderViews.
        """
        from stoqlib.domain.purchase import PurchaseOrderView
        return self.store.find(PurchaseOrderView,
                               supplier_id=self.id).order_by(PurchaseOrderView.open_date)

    def get_last_purchase_date(self):
        """Fetch the date of the last purchased item by this supplier.
        ``None`` is returned if there are no sales yet made by the client.

        :returns: the date of the last purchased item
        :rtype: datetime.date or ``None``
        """
        orders = self.get_supplier_purchases()
        if orders.count():
            # The get_client_sales method already returns a sorted list of
            # sales by open_date column
            # pylint: disable=E1101
            return orders.last().open_date.date()
            # pylint: enable=E1101


@implementer(IActive)
@implementer(IDescribable)
class Employee(Domain):
    """An individual who performs work for an employer under a verbal
    or written understanding where the employer gives direction as to
    what tasks are done
    """

    __storm_table__ = 'employee'

    STATUS_NORMAL = u'normal'
    STATUS_AWAY = u'away'
    STATUS_VACATION = u'vacation'
    STATUS_OFF = u'off'

    statuses = {STATUS_NORMAL: _(u'Normal'),
                STATUS_AWAY: _(u'Away'),
                STATUS_VACATION: _(u'Vacation'),
                STATUS_OFF: _(u'Off')}

    #: normal/away/vacation/off
    status = EnumCol(allow_none=False, default=STATUS_NORMAL)

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #: salary for this employee
    salary = PriceCol(default=0)

    #: when this employeer started working for the |branch|
    admission_date = DateTimeCol(default=None)

    #: when the vaction expires for this employee
    expire_vacation = DateTimeCol(default=None)

    registry_number = UnicodeCol(default=None)
    education_level = UnicodeCol(default=None)
    dependent_person_number = IntCol(default=None)

    role_id = IdCol()

    #: A reference to an employee role object
    role = Reference(role_id, 'EmployeeRole.id')
    is_active = BoolCol(default=True)

    # This is Brazil-specific information
    workpermit_data_id = IdCol(default=None)
    workpermit_data = Reference(workpermit_data_id, 'WorkPermitData.id')
    military_data_id = IdCol(default=None)
    military_data = Reference(military_data_id, 'MilitaryData.id')
    voter_data_id = IdCol(default=None)
    voter_data = Reference(voter_data_id, 'VoterData.id')
    bank_account_id = IdCol(default=None)
    bank_account = Reference(bank_account_id, 'BankAccount.id')

    branch_id = IdCol()

    #: The |branch| this employee works on
    branch = Reference(branch_id, 'Branch.id')

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This employee is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This employee is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    def merge_with(self, other, copy_empty_values=True):
        skip = None

        # To merged employees: change the EmployeeRoleHistory status to inactive.
        # This is necessary to show that the employee has only an active role.
        clause = (EmployeeRoleHistory.employee_id == other.id)
        self.store.execute(Update({EmployeeRoleHistory.is_active: False},
                                  clause, EmployeeRoleHistory))

        super(Employee, self).merge_with(other, skip, copy_empty_values)

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def get_role_history(self):
        return self.store.find(EmployeeRoleHistory,
                               employee=self)

    def get_active_role_history(self):
        store = self.store
        return store.find(EmployeeRoleHistory, employee=self,
                          is_active=True).one()

    @classmethod
    def get_active_employees(cls, store):
        """Return a list of active employees."""
        return store.find(cls,
                          And(cls.status == cls.STATUS_NORMAL,
                              Eq(cls.is_active, True)))


@implementer(IActive)
@implementer(IDescribable)
class LoginUser(Domain):
    """A user that us able to login to the system
    """

    __storm_table__ = 'login_user'

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #: username, used to login it to the system
    username = UnicodeCol()

    #: a hash (md5) for the user password
    pw_hash = UnicodeCol()

    profile_id = IdCol()

    #: A profile represents a colection of information
    #: which represents what this user can do in the system
    profile = Reference(profile_id, 'UserProfile.id')

    is_active = BoolCol(default=True)

    def __init__(self, store=None, **kw):
        if 'password' in kw:
            kw['pw_hash'] = self.hash(kw['password'] or u'')
            del kw['password']
        Domain.__init__(self, store=store, **kw)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This user is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This user is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    def merge_with(self, other, copy_empty_values=True):
        # user_branch_access is unique for (user_id, branch_id), so we should
        # only migrate what the current user does not have (and maybe delete the
        # rest)
        skip = set([('user_branch_access', 'user_id')])
        subselect = Select(columns=[UserBranchAccess.branch_id],
                           tables=[UserBranchAccess],
                           where=(UserBranchAccess.user_id == self.id))
        clause = And(UserBranchAccess.user_id == other.id,
                     NotIn(UserBranchAccess.branch_id, subselect))
        self.store.execute(Update({UserBranchAccess.user_id: self.id},
                                  clause, UserBranchAccess))

        super(LoginUser, self).merge_with(other, skip, copy_empty_values)

    @classmethod
    def hash(cls, password):
        """:returns: the hash of a password.
        """
        assert isinstance(password, unicode)

        return unicode(hashlib.md5(password).hexdigest())

    @classmethod
    def authenticate(cls, store, username, pw_hash, current_branch):
        """Authenticates a user against the credentials passed.
        :returns: A |loginuser| if a user is found, else returns ``None``.
        """
        user = store.find(LoginUser,
                          username=username,
                          pw_hash=pw_hash,
                          is_active=True).one()

        if not user:
            raise LoginError(_("Invalid user or password"))

        # current_branch may not be set if we are registering a new station
        if current_branch and not user.has_access_to(current_branch):
            raise LoginError(_(u'This user does not have access to this '
                               'branch.'))

        return user

    @property
    def status_str(self):
        """Returns the status description of a user"""
        if self.is_active:
            return self.statuses[self.STATUS_ACTIVE]
        return self.statuses[self.STATUS_INACTIVE]

    @classmethod
    def get_active_users(cls, store):
        """Returns a list of all active |loginusers|"""
        return store.find(cls, is_active=True)

    def get_associated_branches(self):
        """ Returns all the |branches| which the user has access
        """
        return self.store.find(UserBranchAccess,
                               user=self)

    def add_access_to(self, branch):
        UserBranchAccess(store=self.store, user=self, branch=branch)

    def has_access_to(self, branch):
        """Checks if the user has access to the given |branch|.

        If the user has access to Administrative App, he has access to any
        |branch|.
        """
        if self.profile.check_app_permission(u'admin'):
            return True
        return UserBranchAccess.has_access(self.store, self, branch)

    def set_password(self, password):
        """Changes the user password.
        """
        self.pw_hash = self.hash(password or u'')

    def login(self):
        station = get_current_station(self.store)
        if station:
            Event.log(self.store,
                      Event.TYPE_USER,
                      _(u"User '%s' logged in on '%s'") % (self.username,
                                                           station.name))
        else:
            Event.log(self.store,
                      Event.TYPE_USER,
                      _(u"User '%s' logged in") % (self.username, ))

    def logout(self):
        station = get_current_station(self.store)
        if station:
            Event.log(self.store,
                      Event.TYPE_USER,
                      _(u"User '%s' logged out from '%s'") % (self.username,
                                                              station.name))
        else:
            Event.log(self.store,
                      Event.TYPE_USER,
                      _(u"User '%s' logged out") % (self.username, ))


@implementer(IActive)
@implementer(IDescribable)
class Branch(Domain):
    """An administrative division of some larger or more complex
    organization
    """

    __storm_table__ = 'branch'

    (STATUS_ACTIVE,
     STATUS_INACTIVE) = range(2)

    statuses = {STATUS_ACTIVE: _(u'Active'),
                STATUS_INACTIVE: _(u'Inactive')}

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    manager_id = IdCol(default=None)

    #: An employee which is in charge of this branch
    manager = Reference(manager_id, 'Employee.id')

    is_active = BoolCol(default=True)

    #: Brazil specific, "Código de Regime Tributário", one of:
    #:
    #: * Simples Nacional
    #: * Simples Nacional – excesso de sublimite da receita bruta
    #: * Regime Normal
    crt = IntCol(default=1)

    #: An acronym that uniquely describes a branch
    acronym = UnicodeCol(default=None)

    #: if this branch can execute |workorders| that belongs to other branches
    can_execute_foreign_work_orders = BoolCol(default=False)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This branch is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This branch is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        person = self.person
        return person.company.fancy_name or person.name

    #
    # Public API
    #

    def merge_with(self, other, copy_empty_values=True):
        # We cannot merge branches right now, since identifiers should be unique
        # by branch and changing identifiers would not be nice.
        assert False

    def set_acronym(self, value):
        """Sets the branch acronym.

        :param value: The new acronym for this branch. If an empty string is
          used, it will be changed to ``None``.
        """
        if value == u'':
            value = None

        self.acronym = value

    def check_acronym_exists(self, acronym):
        """Returns ``True`` if we already have a Company with the given acronym
        in the database.
        """
        return self.check_unique_value_exists(Branch.acronym, acronym)

    def is_from_same_company(self, other_branch):
        """Receives a branch and checks, using this and the other branch's
        cnpj, whether they are from the same company

        :param other_branch: an :class:`branch <Branch>`
        :returns: true if they are from same company, false otherwise
        """
        cnpj = self.person.company.cnpj
        other_cnpj = other_branch.person.company.cnpj

        if not cnpj or not other_cnpj:
            return False

        return cnpj.split(u'/')[0] == other_cnpj.split(u'/')[0]

    # Event

    def on_create(self):
        Event.log(self.store, Event.TYPE_SYSTEM,
                  _(u"Created branch '%s'") % (self.get_description(), ))

    # Classmethods

    @classmethod
    def get_active_branches(cls, store):
        return store.find(cls, Eq(cls.is_active, True))

    @classmethod
    def get_active_remote_branches(cls, store):
        """Find all active branches excluding the current one

        :param store: the store to be used to find the branches
        :returns: a sequence of active |branches|
        """
        branches = cls.get_active_branches(store)
        current_branch = get_current_branch(store)
        return branches.find(Branch.id != current_branch.id)

    @classmethod
    def get_active_items(cls, store):
        """
        Return a list of active items (name, id)

        :param store: a store
        :returns: the items
        """

        join1 = LeftJoin(Person, Person.id == cls.person_id)
        join2 = LeftJoin(Company, Company.person_id == Person.id)
        items = store.using(cls, join1, join2).find((
            Coalesce(Company.fancy_name, Person.name),
            cls.id),
            Eq(cls.is_active, True))
        return locale_sorted(items, key=operator.itemgetter(0))


@implementer(IActive)
@implementer(IDescribable)
class SalesPerson(Domain):
    """An employee in charge of making sales

    """

    __storm_table__ = 'sales_person'

    # Not really used right now
    (COMMISSION_GLOBAL,
     COMMISSION_BY_SALESPERSON,
     COMMISSION_BY_SELLABLE,
     COMMISSION_BY_PAYMENT_METHOD,
     COMMISSION_BY_BASE_SELLABLE_CATEGORY,
     COMMISSION_BY_SELLABLE_CATEGORY,
     COMMISSION_BY_SALE_TOTAL) = range(7)

    comission_types = {COMMISSION_GLOBAL: _(u'Globally'),
                       COMMISSION_BY_SALESPERSON: _(u'By Salesperson'),
                       COMMISSION_BY_SELLABLE: _(u'By Sellable'),
                       COMMISSION_BY_PAYMENT_METHOD: _(u'By Payment Method'),
                       COMMISSION_BY_BASE_SELLABLE_CATEGORY: _(u'By Base '
                                                               u'Sellable '
                                                               u'Category'),
                       COMMISSION_BY_SELLABLE_CATEGORY: _(u'By Sellable '
                                                          u'Category'),
                       COMMISSION_BY_SALE_TOTAL: _(u'By Sale Total')}

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    #: The percentege of commission the company must pay
    #: for this salesman
    comission = PercentCol(default=0)

    #: A rule used to calculate the amount of
    #: commission. This is a reference to another object
    comission_type = IntCol(default=COMMISSION_BY_SALESPERSON)

    is_active = BoolCol(default=True)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This sales person is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This sales person is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_active_salespersons(cls, store):
        """Get a list of all active salespersons

        When the salesperson is also a user in the system, only the users that
        have access to the current branch will be returned

        This will returna list of sales person ready to be used with a
        combo.prefill method
        """
        tables = [SalesPerson,
                  Join(Person, Person.id == SalesPerson.person_id),
                  LeftJoin(LoginUser, LoginUser.person_id == SalesPerson.person_id),
                  LeftJoin(UserBranchAccess, UserBranchAccess.user_id == LoginUser.id)]
        current_branch = get_current_branch(store)
        query = And(
            Eq(cls.is_active, True),
            Or(UserBranchAccess.branch_id == current_branch.id,
               Eq(UserBranchAccess.branch_id, None)))
        items = store.using(*tables).find((Person.name, SalesPerson), query)
        return locale_sorted(items, key=operator.itemgetter(0))

    @classmethod
    def get_active_items(cls, store):
        """
        Return a list of active items (name, id)

        When the salesperson is also a user in the system, only the users that
        have access to the current branch will be returned

        :param store: a store
        :returns: the items
        """
        return [(name, salesperson.id) for name, salesperson in
                cls.get_active_salespersons(store)]


@implementer(IActive)
@implementer(IDescribable)
class Transporter(Domain):
    """An individual or company engaged in the transportation
    """

    __storm_table__ = 'transporter'

    person_id = IdCol()

    #: the |person|
    person = Reference(person_id, 'Person.id')

    is_active = BoolCol(default=True)

    #: The date when we start working with this transporter
    open_contract_date = DateTimeCol(default_factory=localnow)

    # FIXME: not used in purchases.
    #: The percentage amount of freight charged by this transporter
    freight_percentage = PercentCol(default=0)

    #
    # IActive
    #

    def inactivate(self):
        assert self.is_active, (u'This transporter is already inactive')
        self.is_active = False

    def activate(self):
        assert not self.is_active, (u'This transporter is already active')
        self.is_active = True

    def get_status_string(self):
        if self.is_active:
            return _(u'Active')
        return _(u'Inactive')

    #
    # IDescribable
    #

    def get_description(self):
        return self.person.name

    #
    # Public API
    #

    @classmethod
    def get_active_transporters(cls, store):
        """Get a list of all available transporters"""
        query = Eq(cls.is_active, True)
        return store.find(cls, query)

    @classmethod
    def get_active_items(cls, store):
        """
        Return a list of active items (name, id)

        :param store: a store
        :returns: the items
        """
        join1 = LeftJoin(Person, Person.id == cls.person_id)
        items = store.using(cls, join1).find((
            Person.name,
            cls.id),
            Eq(cls.is_active, True))
        return locale_sorted(items, key=operator.itemgetter(0))


class EmployeeRoleHistory(Domain):
    """Base class to store the employee role history."""

    __storm_table__ = 'employee_role_history'

    began = DateTimeCol(default_factory=localnow)
    ended = DateTimeCol(default=None)
    salary = PriceCol()
    role_id = IdCol()
    role = Reference(role_id, 'EmployeeRole.id')
    employee_id = IdCol()
    employee = Reference(employee_id, 'Employee.id')
    is_active = BoolCol(default=True)


class ClientSalaryHistory(Domain):
    """A class to keep track of all the salaries a client has had
    """

    __storm_table__ = 'client_salary_history'

    #: date when salary has been updated
    date = DateTimeCol()

    #: value of the updated salary
    new_salary = PriceCol()

    #: value of the previous salary
    old_salary = PriceCol()

    client_id = IdCol()

    #: the |client| whose salary is being stored
    client = Reference(client_id, 'Client.id')

    user_id = IdCol()

    #: the |loginuser| who updated the salary
    user = Reference(user_id, 'LoginUser.id')

    @classmethod
    def add(cls, store, old_salary, client, user):
        if old_salary != client.salary:
            ClientSalaryHistory(store=store,
                                date=localtoday().date(),
                                new_salary=client.salary,
                                old_salary=old_salary,
                                client=client,
                                user=user)


class UserBranchAccess(Domain):
    """This class associates a |loginuser| to a |branch|.

    Users will only be able to login into Stoq if it is associated with the
    computer's branch.
    """

    __storm_table__ = 'user_branch_access'

    user_id = IdCol()

    #: the |loginuser|
    user = Reference(user_id, 'LoginUser.id')

    branch_id = IdCol()

    #: the |branch|
    branch = Reference(branch_id, 'Branch.id')

    @classmethod
    def has_access(cls, store, user, branch):
        """Checks if the given user has access to the given branch
        """
        return store.find(cls, user=user, branch=branch).one() is not None


#
# Views
#


@implementer(IDescribable)
class ClientView(Viewable):
    """Stores information about clients.

    Available fields are:
    :attribute id: id of the client table
    :attribute name: client name
    :attribute status: client financial status
    :attribute cpf: brazil-specific cpf attribute
    :attribute rg: brazil-specific rg_number attribute
    :attribute phone_number: client phone_number
    :attribute mobile_number: client mobile_number
    """

    client = Client
    person = Person
    category = ClientCategory

    # Client
    id = Client.id
    status = Client.status

    # Person
    name = Person.name
    person_id = Person.id
    phone_number = Person.phone_number
    mobile_number = Person.mobile_number

    # Company
    fancy_name = Company.fancy_name
    cnpj = Company.cnpj

    # Individual
    cpf = Individual.cpf
    birth_date = Individual.birth_date
    rg_number = Individual.rg_number

    # ClientCategory
    client_category = ClientCategory.name

    # Address
    street = Address.street
    streetnumber = Address.streetnumber
    district = Address.district

    tables = [
        Client,
        Join(Person,
             Person.id == Client.person_id),
        LeftJoin(Individual,
                 Person.id == Individual.person_id),
        LeftJoin(Company,
                 Person.id == Company.person_id),
        LeftJoin(ClientCategory,
                 Client.category_id == ClientCategory.id),
        LeftJoin(Address,
                 And(Address.person_id == Person.id,
                     Eq(Address.is_main_address, True))),
    ]

    clause = Eq(Person.merged_with_id, None)

    #
    # IDescribable
    #

    def get_description(self):
        return self.description

    @property
    def description(self):
        return self.name + (self.fancy_name
                            and u" (%s)" % self.fancy_name or u"")

    #
    # Public API
    #

    @property
    def status_str(self):
        return Client.statuses[self.status]

    @property
    def cnpj_or_cpf(self):
        return self.cnpj or self.cpf

    @classmethod
    def get_active_clients(cls, store):
        """Return a list of active clients.
        An active client is a person who are authorized to make new sales
        """
        return store.find(
            cls, cls.status != Client.STATUS_INACTIVE
        ).order_by(cls.name)


@implementer(IDescribable)
class EmployeeView(Viewable):

    employee = Employee

    id = Employee.id
    person_id = Person.id
    name = Person.name
    role = EmployeeRole.name
    status = Employee.status
    is_active = Employee.is_active
    registry_number = Employee.registry_number

    tables = [
        Employee,
        Join(Person, Person.id == Employee.person_id),
        Join(EmployeeRole, Employee.role_id == EmployeeRole.id),
    ]

    clause = Eq(Person.merged_with_id, None)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    def get_status_string(self):
        return Employee.statuses[self.status]

    @classmethod
    def get_active_employees(cls, store):
        """Return a list of active employees."""
        return store.find(cls, status=Employee.STATUS_NORMAL,
                          is_active=True)


@implementer(IDescribable)
class SupplierView(Viewable):

    supplier = Supplier

    # Supplier
    id = Supplier.id
    status = Supplier.status

    # Person
    person_id = Person.id
    name = Person.name
    phone_number = Person.phone_number
    mobile_number = Person.mobile_number

    # Company
    fancy_name = Company.fancy_name
    cnpj = Company.cnpj

    # Individual
    cpf = Individual.cpf
    birth_date = Individual.birth_date
    rg_number = Individual.rg_number

    # Address
    street = Address.street
    streetnumber = Address.streetnumber
    district = Address.district

    tables = [
        Supplier,
        Join(Person,
             Person.id == Supplier.person_id),
        LeftJoin(Company,
                 Person.id == Company.person_id),
        LeftJoin(Individual,
                 Person.id == Individual.person_id),
        LeftJoin(Address,
                 And(Address.person_id == Person.id,
                     Eq(Address.is_main_address, True))),
    ]

    clause = Eq(Person.merged_with_id, None)

    #
    # IDescribable
    #

    def get_description(self):
        if self.fancy_name:
            return "%s (%s)" % (self.name, self.fancy_name)
        else:
            return self.name

    #
    # Public API
    #

    def get_status_string(self):
        return Supplier.statuses[self.status]


@implementer(IDescribable)
class TransporterView(Viewable):
    """
    Stores information about transporters

    :cvar id: the id of transporter table
    :cvar name: the transporter name
    :cvar phone_number: the transporter phone number
    :cvar person_id: the id of person table
    :cvar status: the current status of the transporter
    :cvar freight_percentage: the freight percentage charged
    """

    transporter = Transporter

    id = Transporter.id
    person_id = Person.id
    name = Person.name
    phone_number = Person.phone_number
    freight_percentage = Transporter.freight_percentage
    is_active = Transporter.is_active

    tables = [
        Transporter,
        Join(Person, Person.id == Transporter.person_id),
    ]

    clause = Eq(Person.merged_with_id, None)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name


@implementer(IDescribable)
class BranchView(Viewable):
    Manager_Person = ClassAlias(Person, 'person_manager')

    branch = Branch

    id = Branch.id
    acronym = Branch.acronym
    is_active = Branch.is_active
    person_id = Person.id
    name = Person.name
    fancy_name = Company.fancy_name
    phone_number = Person.phone_number
    manager_name = Manager_Person.name

    tables = [
        Branch,
        Join(Person, Person.id == Branch.person_id),
        LeftJoin(Company, Company.person_id == Person.id),
        LeftJoin(Employee, Branch.manager_id == Employee.id),
        LeftJoin(Manager_Person, Employee.person_id == Manager_Person.id),
    ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def status_str(self):
        if self.is_active:
            return _(u'Active')

        return _(u'Inactive')


@implementer(IDescribable)
class UserView(Viewable):
    """
    Retrieves information about user in the system.

    :cvar id: the id of user table
    :cvar name: the user full name
    :cvar is_active: the current status of the transporter
    :cvar username: the username (login)
    :cvar person_id: the id of person table
    :cvar profile_id: the id of the user profile
    :cvar profile_name: the name of the user profile (eg: Salesperson)
    """

    user = LoginUser

    id = LoginUser.id
    person_id = Person.id
    name = Person.name
    is_active = LoginUser.is_active
    username = LoginUser.username
    profile_id = LoginUser.profile_id
    profile_name = UserProfile.name

    tables = [
        LoginUser,
        Join(Person, Person.id == LoginUser.person_id),
        LeftJoin(UserProfile, LoginUser.profile_id == UserProfile.id),
    ]

    clause = Eq(Person.merged_with_id, None)

    #
    # IDescribable
    #

    def get_description(self):
        return self.name

    #
    # Public API
    #

    @property
    def status_str(self):
        if self.is_active:
            return _(u'Active')

        return _(u'Inactive')


class CreditCheckHistoryView(Viewable):
    """A view that displays client credit history
    """

    User_Person = ClassAlias(Person, 'user_person')

    check_history = CreditCheckHistory

    id = CreditCheckHistory.id
    _person_id = Person.id
    client_name = Person.name
    check_date = CreditCheckHistory.check_date
    identifier = CreditCheckHistory.identifier
    status = CreditCheckHistory.status
    notes = CreditCheckHistory.notes
    user = User_Person.name

    tables = [
        CreditCheckHistory,
        LeftJoin(Client, Client.id == CreditCheckHistory.client_id),
        LeftJoin(Person, Person.id == Client.person_id),
        LeftJoin(LoginUser, LoginUser.id == CreditCheckHistory.user_id),
        LeftJoin(User_Person, LoginUser.person_id == User_Person.id),
    ]

    #
    # Public API
    #

    @classmethod
    def find_by_client(cls, store, client):
        resultset = store.find(cls)
        if client is not None:
            resultset = resultset.find(CreditCheckHistory.client == client)
        return resultset


@implementer(IDescribable)
class CallsView(Viewable):
    """Store information about the realized calls to client.
    """

    Attendant_Person = ClassAlias(Person, 'attendant_person')

    call = Calls
    person = Person

    id = Calls.id
    person_id = Person.id
    name = Person.name
    date = Calls.date
    description = Calls.description
    message = Calls.message
    attendant = Attendant_Person.name

    tables = [
        Calls,
        LeftJoin(Person, Person.id == Calls.person_id),
        LeftJoin(LoginUser, LoginUser.id == Calls.attendant_id),
        LeftJoin(Attendant_Person, LoginUser.person_id == Attendant_Person.id),
    ]

    #
    # IDescribable
    #

    def get_description(self):
        return self.description

    #
    # Public API
    #

    @classmethod
    def find_by_client_date(cls, store, client, date):
        queries = []
        if client:
            queries.append(Calls.person == client)

        if date:
            if isinstance(date, tuple):
                date_query = And(Date(Calls.date) >= date[0],
                                 Date(Calls.date) <= date[1])
            else:
                date_query = Date(Calls.date) == date

            queries.append(date_query)

        if queries:
            return store.find(cls, And(*queries))

        return store.find(cls)

    @classmethod
    def find_by_date(cls, store, date):
        return cls.find_by_client_date(store, None, date)


class ClientCallsView(CallsView):
    tables = CallsView.tables[:]
    tables.append(
        Join(Client, Client.person_id == Person.id))


class ClientSalaryHistoryView(Viewable):
    """Store information about a client's salary history
    """

    id = ClientSalaryHistory.id
    date = ClientSalaryHistory.date
    new_salary = ClientSalaryHistory.new_salary
    user = Person.name

    tables = [
        ClientSalaryHistory,
        LeftJoin(LoginUser, LoginUser.id == ClientSalaryHistory.user_id),
        LeftJoin(Person, LoginUser.person_id == Person.id),
    ]

    @classmethod
    def find_by_client(cls, store, client):
        resultset = store.find(cls)
        if client is not None:
            resultset = resultset.find(ClientSalaryHistory.client == client)
        return resultset


_InPaymentSummary = Select(
    columns=[PaymentGroup.payer_id,
             Alias(Sum(Payment.paid_value), 'paid_value')],
    tables=[Payment,
            Join(PaymentGroup, PaymentGroup.id == Payment.group_id),
            Join(PaymentMethod, PaymentMethod.id == Payment.method_id)],
    where=And(Payment.payment_type == Payment.TYPE_IN,
              PaymentMethod.method_name == u'credit',
              Payment.status == Payment.STATUS_PAID),
    group_by=[PaymentGroup.payer_id])

_OutPaymentSummary = Select(
    columns=_InPaymentSummary.columns,
    tables=_InPaymentSummary.tables,
    group_by=_InPaymentSummary.group_by,
    where=And(Payment.payment_type == Payment.TYPE_OUT,
              PaymentMethod.method_name == u'credit',
              Payment.status == Payment.STATUS_PAID))


class ClientsWithCreditView(Viewable):
    """A view that displays client with credit
    """
    id = Client.id
    name = Person.name
    phone = Person.phone_number
    email = Person.email
    cpf = Individual.cpf
    birth_date = Individual.birth_date
    cnpj = Company.cnpj
    category = ClientCategory.name

    credit_received = Field('_out_summary', 'paid_value')
    credit_spent = Coalesce(Field('_in_summary', 'paid_value'), 0)
    remaining_credit = credit_received - credit_spent

    tables = [
        Client,
        Join(Person, Person.id == Client.person_id),
        LeftJoin(ClientCategory, ClientCategory.id == Client.category_id),
        LeftJoin(Individual, Individual.person_id == Person.id),
        LeftJoin(Company, Company.person_id == Person.id),
        LeftJoin(Alias(_InPaymentSummary, '_in_summary'),
                 Field('_in_summary', 'payer_id') == Person.id),
        LeftJoin(Alias(_OutPaymentSummary, '_out_summary'),
                 Field('_out_summary', 'payer_id') == Person.id),
    ]

    clause = Or(credit_spent > 0, credit_received > 0)


class PersonAddressView(Viewable):
    person = Person
    main_address = Address

    id = Person.id
    name = Person.name
    phone_number = Person.phone_number
    mobile_number = Person.mobile_number
    fax_number = Person.fax_number
    email = Person.email
    cnpj = Company.cnpj
    cpf = Individual.cpf
    birth_date = Individual.birth_date
    rg_number = Individual.rg_number

    clean_name = StoqNormalizeString(Person.name)
    clean_street = Coalesce(StoqNormalizeString(Address.street), u'')

    tables = [
        Person,
        LeftJoin(Individual,
                 Person.id == Individual.person_id),
        LeftJoin(Company,
                 Person.id == Company.person_id),
        LeftJoin(Address,
                 And(Address.person_id == Person.id,
                     Eq(Address.is_main_address, True))),
    ]

    clause = Eq(Person.merged_with_id, None)
