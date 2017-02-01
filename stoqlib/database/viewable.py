# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Viewable implementation using python

Using Viewable, you can create an special object that will have properties from
different tables, for instance, given this to ORM classes:

   >>> from storm.expr import LeftJoin, Count, Sum
   >>> from stoqlib.api import api
   >>> from stoqlib.database.orm import ORMObject
   >>> from stoqlib.database.properties import DecimalCol, DateTimeCol
   >>> from stoqlib.database.properties import IntCol, UnicodeCol, IdCol

   >>> class Person(ORMObject):
   ...     __storm_table__ = 'person'
   ...     id = IdCol(primary=True)
   ...     name = UnicodeCol()

   >>> class Client(ORMObject):
   ...     __storm_table__ = 'client'
   ...     id = IdCol(primary=True)
   ...     person_id = IdCol()
   ...     salary = DecimalCol()
   ...     status = IntCol()

You can create a viewable like this:

    >>> class ClientView(Viewable):
    ...     id = Client.id
    ...     name = Person.name
    ...     salary = Client.salary
    ...
    ...     tables = [Client,
    ...               LeftJoin(Person, Person.id == Client.person_id)]

And use it like a regular table with storm:

    >>> store = api.new_store()
    >>> for v in store.find(ClientView).order_by(Person.name):
    ...     print v.name, v.salary
    Alessandra Almeida Itaberá 0.00
    Franciso Elisio de Lima Junior 0.00
    Luis Sergio da Silva Marin 0.00
    Vitalina Claudino 0.00

You can also define another class as properties of the viewable. For instance:

    >>> class ClientView(Viewable):
    ...     client = Client
    ...     person = Person
    ...
    ...     name = Person.name
    ...     nick = Client.salary
    ...
    ...     tables = [Client,
    ...               LeftJoin(Person, Person.id == Client.person_id)]

When you query using this viewable, not only the name and nick properties
will be fetched, but the whole Client and Person objects will be also fetched
(on the same sql select), and the objects will be added to the cache, so you can
use them later, without going to the database for another query.

Another interesting feature is the possiblity to use aggregates in the viewable.
Lets consider this sales table:

    >>> class Sale(ORMObject):
    ...     __storm_table__ = 'sale'
    ...     id = IdCol(primary=True)
    ...     client_id = IdCol()
    ...     total_amount = DecimalCol()
    ...     status = IntCol()

Now we can create this viewable:


    >>> class ClientSalesView(Viewable):
    ...    id = Client.id
    ...    name = Person.name
    ...    total_sales = Count(Sale.id)
    ...    total_value = Sum(Sale.total_amount)
    ...
    ...    tables = [Client,
    ...              LeftJoin(Person, Person.id == Client.person_id),
    ...              LeftJoin(Sale, Sale.client_id == Client.id)]
    ...
    ...    group_by = [id, name]

    >>> store = api.new_store()
    >>> for v in store.find(ClientSalesView).order_by(Person.name):
    ...     print v.name, v.total_sales, v.total_value
    Alessandra Almeida Itaberá 1 706.00
    Franciso Elisio de Lima Junior 0 None
    Luis Sergio da Silva Marin 1 873.00
    Vitalina Claudino 1 436.00

    >>> store.close()

"""

import inspect
import warnings

from kiwi.python import ClassInittableObject
from storm.expr import Expr, JoinExpr
from storm.properties import PropertyColumn

from stoqlib.database.orm import ORMObject


class Viewable(ClassInittableObject):
    # This is only used by query executer, and can be removed once all viewables
    # are converted to the new api
    __storm_table__ = 'viewable'

    #: This is the cls_spec that should be used with store.find(). Will be
    #: created by StoqlibStore when the viewable is first used.
    cls_spec = None

    #: Corresponding attributes for each cls_spec. Will be created by
    #: StoqlibStore when the viewable is first used.
    cls_attributes = None

    #: A list of tables that will be queried, Viewable subclasses should
    # normally make a copy of this to avoid clobbering up the tables of the
    # parent class(es)
    tables = []

    #: If any property defined in this viewable is an aggregate funcion (that
    #: needs grouping), this should have all the columns or table that should be
    #: grouped.
    group_by = []

    #: If not ``None``, this will be appended to the query passed to
    #: store.find()
    clause = None

    #: If not ``None``, this will be used to filter the query using HAVING
    having = None

    #: This is a list of column names that should not be selected, but should
    #: still be possible to filter by.
    hidden_columns = []

    @property
    def store(self):
        warnings.warn("Dont use self.store - get it from some other object)",
                      DeprecationWarning, stacklevel=2)
        return self._store

    # Maybe we could try to use the same api from storm (autoreload)
    def sync(self):
        """Update the values of this object from the database
        """
        new_obj = self._store.find(type(self), id=self.id).one()
        self.__dict__.update(new_obj.__dict__)

    def __hash__(self):
        if hasattr(self, 'id'):
            return hash(self.id)
        return super(Viewable, self).__hash__()

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.id == other.id
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def __class_init__(cls, new_attrs):
        cls_spec = []
        attributes = []

        # We can ignore the last three items, since they are: the Viewable class
        # kwi.ClassInitiableObject and ``object``
        for base in inspect.getmro(cls)[:-3]:
            for attr, value in base.__dict__.items():
                if attr == 'clause':
                    continue
                if attr in cls.hidden_columns:
                    continue

                try:
                    is_domain = issubclass(value, ORMObject)
                except TypeError:
                    is_domain = False

                # XXX: This is to workaround the viewables sometimes defining
                # aliases for some tables - They are valid domain classes, but
                # should not be used in the store.find() call
                if is_domain and value.__name__.endswith('Alias'):
                    continue

                is_column = isinstance(value, PropertyColumn)
                if is_column:
                    vf = value.variable_factory
                    # Storm suffers from a bug that, if a column defines
                    # "allow_none=False", it will fail when it is retrieved
                    # from the database as NULL. That is something very common
                    # for viewables doing left joins and it should not fail.
                    # To workaround that, lets create a copy of it and remove
                    # the allow_none keyword from the property
                    if not vf.keywords.get('allow_none', True):
                        keywords = vf.keywords.copy()

                        # We want to remove allow_none so it will assume its
                        # default form (True). Also, validator_attribute should
                        # be passed on the constructor and column will be
                        # passed to variable_factory as "self" inside the
                        # PropertyColumn.
                        validator_attribute = keywords.pop('validator_attribute')
                        for kw in ['allow_none', 'column']:
                            keywords.pop(kw, None)

                        # This is a copy of how the PropertyColumn is created
                        # by Storm, passing exactly the same arguments. The
                        # resulting object should be identical to the original
                        value = PropertyColumn(
                            value, value.cls, validator_attribute,
                            value.name, value.primary, vf.func, keywords)
                        setattr(cls, attr, value)

                if (attr not in attributes and (is_domain or is_column or
                                                isinstance(value, Expr))):
                    attributes.append(attr)
                    cls_spec.append(value)

        cls.cls_spec = tuple(cls_spec)
        cls.cls_attributes = attributes

        # We store highjacked classes in this dict. Highjacked viewables
        # are the ones that we create programatically changing one or another
        # attribute (e.g. a join). See ProductFullStockView for more details
        cls.highjacked = {}

    @classmethod
    def extend_viewable(cls, new_attrs, new_joins=None):
        """Creates a subclass of this extended with the given columns and joins

        This method will return a new Viewable class that is a subclass of
        the current viewable, extended with the new attributes and joins.

        :param new_attrs: A dictionary with the attributes that should be added
          to the new viewable
        :param new_joins: A list of new joins that should be appended to the new
          viewable
        """
        # Create a new viewable as a subclass of the original viewable, that
        # inclues the new tables
        klass_dict = dict(
            tables=cls.tables + (new_joins or []),
            **new_attrs)

        if cls.group_by:
            klass_dict['group_by'] = cls.group_by[:] + new_attrs.values()

        return type(cls.__name__ + 'Ext', (cls, ), klass_dict)

    @classmethod
    def has_join_with(cls, table):
        """Checks if this view has a join with some table.

        This will look at all the joins of the viewable and return True if the
        given table is in one of the joins, and False otherwise

        :param table: Table that is performed Join.
        """
        for i in cls.tables:
            if not isinstance(i, JoinExpr):
                if i is table:
                    return True
            elif table in (i.left, i.right):
                return True
        return False

    @classmethod
    def has_column(cls, column):
        """Checks if the given column is selected in this view.

        This will look at all the selected columns and return True if the given
        one is one of them, False otherwise.
        Note that this will not work for storm expressions (like Sum or Count)

        :param column: The column to be searched.
        """
        for col in cls.cls_spec:
            if col is column:
                return True
        return False
