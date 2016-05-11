# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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
"""
The base :class:`Domain` class for Stoq.

"""

import logging
import warnings

from storm.exceptions import NotOneError
from storm.expr import And, Alias, Like, Max, Select, Update
from storm.info import get_cls_info, get_obj_info
from storm.properties import Property
from storm.references import Reference
from storm.store import AutoReload, PENDING_ADD, PENDING_REMOVE

from stoqlib.database.expr import CharLength, Field, LPad, UnionAll
from stoqlib.database.orm import ORMObject
from stoqlib.database.properties import IntCol, IdCol, UnicodeCol, Identifier
from stoqlib.domain.events import DomainMergeEvent
from stoqlib.domain.system import TransactionEntry

log = logging.getLogger(__name__)


(_OBJ_CREATED,
 _OBJ_DELETED,
 _OBJ_UPDATED) = range(3)


class Domain(ORMObject):
    """The base domain for Stoq.

    This builds on top of :class:`stoqlib.database.properties.ORMObject` and adds:

    * created and modified |transactionentry|, a log which is mainly used
      by database synchonization, it allows us to find out what has been
      modified and created within a specific time frame.
    * create/update/modify hooks, which some domain objects implement to
      fire of events that can be used to find out when a specific
      domain event is triggered, eg a |sale| is created, a |product| is
      modified. etc.
    * cloning of domains, when you want to create a new similar domain
    * function to check if an value of a column is unique within a domain.

    Not all domain objects need to subclass Domain, some, such as
    :class:`stoqlib.domain.system.SystemTable` inherit from ORMObject.
    """

    # FIXME: this is only used by pylint
    __storm_table__ = 'invalid'

    #: A list of fields from this object that should de added on the
    #: representation of this object (when calling repr())
    repr_fields = []

    #: id of this domain class, it's usually the primary key.
    #: it will automatically update when a new insert is created.
    #: Note that there might be holes in the sequence numbers, which happens
    #: due to aborted transactions
    id = IdCol(primary=True, default=AutoReload)

    te_id = IntCol(default=AutoReload)

    #: a |transactionentry| for when the domain object was created and last
    #: modified
    te = Reference(te_id, TransactionEntry.id)

    def __init__(self, *args, **kwargs):
        self._listen_to_events()
        ORMObject.__init__(self, *args, **kwargs)

    def __repr__(self):
        parts = ['%r' % self.id]
        for field in self.repr_fields:
            parts.append('%s=%r' % (field, getattr(self, field)))

        desc = ' '.join(parts)
        return '<%s %s>' % (self.__class__.__name__, desc)

    def __storm_loaded__(self):
        self._listen_to_events()

    def __storm_pre_flush__(self):
        obj_info = get_obj_info(self)
        pending = obj_info.get("pending")
        stoq_pending = obj_info.get('stoq-status')
        store = obj_info.get("store")

        if pending is PENDING_ADD:
            obj_info['stoq-status'] = _OBJ_CREATED
        elif pending is PENDING_REMOVE:
            obj_info['stoq-status'] = _OBJ_DELETED
        else:
            # This is storm's approach to check if the obj has pending changes,
            # but only makes sense if the obj is not being created/deleted.
            if (store._get_changes_map(obj_info, True) and
                    stoq_pending not in [_OBJ_CREATED, _OBJ_DELETED]):
                obj_info['stoq-status'] = _OBJ_UPDATED

    #
    #   Private
    #

    def _listen_to_events(self):
        event = get_obj_info(self).event
        event.hook('before-removed', self._on_object_before_removed)
        event.hook('before-commited', self._on_object_before_commited)

    def _on_object_before_removed(self, obj_info):
        # If the obj was created and them removed, nothing needs to be done.
        # It never really got into the database.
        if obj_info.get('stoq-status') == _OBJ_CREATED:
            obj_info['stoq-status'] = None
        else:
            self.on_delete()

        # This is emited right before the object is removed from the store.
        # We must also remove the transaction entry, but the entry should be
        # deleted *after* the object is deleted, thats why we need to specify
        # the flush order.
        store = obj_info.get("store")
        store.remove(self.te)
        store.add_flush_order(self, self.te)

    def _on_object_before_commited(self, obj_info):
        # on_create/on_update hooks can modify the object and make it be
        # flushed again, so lets reset pending before calling them
        stoq_pending = obj_info.get('stoq-status')
        obj_info['stoq-status'] = None

        if stoq_pending == _OBJ_CREATED:
            self.on_create()
        elif stoq_pending == _OBJ_UPDATED:
            self.on_update()

    #
    # Public API
    #

    def serialize(self):
        """Returns the object as a dictionary"""
        dictionary = {}
        for cls in self.__class__.__mro__:
            for key, value in cls.__dict__.iteritems():
                if isinstance(value, Property):
                    attribute = getattr(self, key)
                    # Handle Identifier Columns as string instead of int
                    if type(attribute) == Identifier:
                        attribute = str(attribute)
                    dictionary[key] = attribute
        return dictionary

    def on_create(self):
        """Called when *self* is about to be created on the database

        This hook can be overridden on child classes for improved functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and do your modifications in it.
        """

    def on_update(self):
        """Called when *self* is about to be updated on the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and do your modifications in it.
        """

    def on_delete(self):
        """Called when *self* is about to be removed from the database

        This hook can be overridden on child classes for improved
        functionality.

        A trick you may want to use: Use :meth:`ORMObject.get_store` to get the
        :class:`store <stoqlib.database.runtime.StoqlibStore>` in which
        *self* lives and use it to do a cleanup in other objects for instance,
        so if the store is rolled back, your cleanup will be rolled back too.

        Note that modifying *self* doesn't make sense since it will soon be
        removed from the database.
        """

    def clone(self):
        """Get a persistent copy of an existent object. Remember that we can
        not use copy because this approach will not activate ORMObject
        methods which allow creating persitent objects. We also always
        need a new id for each copied object.

        :returns: the copy of ourselves
        """
        warnings.warn("don't use this", DeprecationWarning, stacklevel=2)
        kwargs = {}
        for column in get_cls_info(self.__class__).columns:
            # FIXME: Make sure this is cloning correctly
            name = column.name
            if name in ['id', 'identifier',
                        'te_id']:
                continue
            if name.endswith('_id'):
                name = name[:-3]
            kwargs[name] = getattr(self, name)

        klass = type(self)
        return klass(store=self.store, **kwargs)

    def check_unique_value_exists(self, attribute, value,
                                  case_sensitive=True):
        """Check database for attribute/value precense

        Check if we already the given attribute/value pair in the database,
        but ignoring this object's ones.

        :param attribute: the attribute that should be unique
        :param value: value that we will check if exists in the database
        :param case_sensitive: If the checking should be case sensitive or
          not.
        :returns: the existing object or ``None``
        """
        return self.check_unique_tuple_exists({attribute: value},
                                              case_sensitive)

    def check_unique_tuple_exists(self, values, case_sensitive=True):
        """Check database for values presence

        Check if we already the given attributes and values in the database,
        but ignoring this object's ones.

        :param values: dictionary of attributes:values that we will check if
          exists in the database.
        :param case_sensitive: If the checking should be case sensitive or
          not.
        :returns: the existing object or ``None``
        """
        if all([value in ['', None] for value in values.values()]):
            return None

        clauses = []
        for attr, value, in values.items():
            self.__class__.validate_attr(attr)

            if not isinstance(value, unicode) or case_sensitive:
                clauses.append(attr == value)
            else:
                clauses.append(Like(attr, value, case_sensitive=False))

        cls = type(self)
        # Remove myself from the results.
        if hasattr(self, 'id'):
            clauses.append(cls.id != self.id)
        query = And(*clauses)

        try:
            return self.store.find(cls, query).one()
        except NotOneError:
            # FIXME: Instead of breaking stoq if more than one tuple exists,
            # simply return the first object, but log a warning about the
            # database issue. We should have UNIQUE constraints in more places
            # to be sure that this would never happen
            values_str = ["%s => %s" % (k.name, v) for k, v in values.items()]
            log.warning(
                "more than one result found when trying to "
                "check_unique_tuple_exists on table '%s' for values: %r" % (
                    self.__class__.__name__, ', '.join(sorted(values_str))))
            return self.store.find(cls, query).any()

    def merge_with(self, other, skip=None, copy_empty_values=True):
        """Does automatic references updating when merging two objects.

        This will update all tables that reference the `other` object and make
        them reference `self` instead.

        After this it should be safe to remove the `other` object. Since there
        is no one referencing it anymore.

        :param skip: A set of (table, column) that should be skiped by the
          automatic update. This are normally tables that require a special
          treatment, like when there are constraints.
        :param copy_empty_values: If True, attributes that are either null or an
          empty string in self will be updated with the value from the other
          object (given that the other attribute is not empty as well)
        """
        skip = skip or set()
        event_skip = DomainMergeEvent.emit(self, other)
        if event_skip:
            skip = skip.union(event_skip)

        if copy_empty_values:
            self.copy_empty_values(other)

        refs = self.store.list_references(type(self).id)
        for (table, column, other_table, other_column, u, d) in refs:
            if (table, column) in skip:
                continue

            clause = Field(table, column) == other.id
            self.store.execute(Update({column: self.id}, clause, table))

    def copy_empty_values(self, other):
        """Copies the values from other object if missing in self

        This will copy all values from the other object that are missing from
        this one.
        """
        empty_values = [None, u'']
        for attr_property, column in self._storm_columns.items():
            self_value = getattr(self, column.name)
            other_value = getattr(other, column.name)
            if self_value in empty_values and other_value not in empty_values:
                setattr(self, column.name, other_value)

    def can_remove(self, skip=None):
        """Check if this object can be removed from the database

        This will check if there's any object referencing self

        :param skip: an itarable containing the (table, column) to skip
            the check. Use this to avoid false positives when you will
            delete those skipped by hand before self.
        """
        skip = skip or set()
        selects = []
        refs = self.store.list_references(self.__class__.id)

        for t_name, c_name, ot_name, oc_name, u, d in refs:
            if (t_name, c_name) in skip:
                continue

            column = Field(t_name, c_name)
            selects.append(
                Select(columns=[1], tables=[t_name],
                       where=column == self.id, limit=1))

        # If everything was skipped, there's no query to execute
        if not len(selects):
            return True

        # We can only pass limit=1 to UnionAll if there's more than one select.
        # If not, storm will put the limit anyway and it will join with the
        # select's limit producing an error: multiple LIMIT clauses not allowed
        if len(selects) > 1:
            extra = {'limit': 1}
        else:
            extra = {}

        return not any(self.store.execute(UnionAll(*selects, **extra)))

    #
    #  Classmethods
    #

    @classmethod
    def get_temporary_identifier(cls, store):
        """Returns a temporary negative identifier

        This should be used when working with syncronized databases and a
        purchase order is being created in a branch different than the
        destination branch.

        The sincronizer will be responsible for setting the definitive
        identifier once the order arives at the destination
        """
        lower_value = store.find(cls).min(cls.identifier)
        return min(lower_value, 0) - 1

    @classmethod
    def find_distinct_values(cls, store, attr, exclude_empty=True):
        """Find distinct values for a given attr

        :param store: a store
        :param attr: the attr we are going to get distinct values for
        :param exclude_empty: if ``True``, empty results (``None`` or
            empty strings) will be removed from the results
        :returns: an iterator of the results
        """
        cls.validate_attr(attr)

        results = store.find(cls)
        results.config(distinct=True)
        for value in results.values(attr):
            if exclude_empty and not value:
                continue
            yield value

    @classmethod
    def get_max_value(cls, store, attr, validate_attr=True):
        """Get the maximum value for a given attr

        On text columns, trying to find the max value for them using MAX()
        on postgres would result in some problems, like '9' being considered
        greater than '10' (because the comparison is done from left to right).

        This will 0-"pad" the values for the comparison, making it compare
        the way we want. Note that because of that, in the example above,
        it would return '09' instead of '9'

        :para store: a store
        :param attr: the attribute to find the max value for
        :returns: the maximum value for the attr
        """
        if validate_attr:
            cls.validate_attr(attr, expected_type=UnicodeCol)

        max_length = Alias(
            Select(columns=[Alias(Max(CharLength(attr)), 'max_length')],
                   tables=[cls]),
            '_max_length')
        # Using LPad with max_length will workaround most of the cases where
        # the string comparison fails. For example, the common case would
        # consider '9' to be greater than '10'. We could test just strings
        # with length equal to max_length, but than '010' would be greater
        # than '001' would be greater than '10' (that would be excluded from
        # the comparison). By doing lpad, '09' is lesser than '10' and '001'
        # is lesser than '010', working around those cases
        max_batch = store.using(cls, max_length).find(cls).max(
            LPad(attr, Field('_max_length', 'max_length'), u'0'))

        # Make the api consistent and return an ampty string instead of None
        # if there's no batch registered on the database
        return max_batch or u''

    @classmethod
    def get_or_create(cls, store, **kwargs):
        """Get the object from the database that matches the given criteria, and if
        it doesn't exist, create a new object, with the properties given already
        set.

        The properties given ideally should be the primary key, or a candidate
        key (unique values).

        :returns: an object matching the query or a newly created one if a
          matching one couldn't be found.
        """
        obj = store.find(cls, **kwargs).one()
        if obj is not None:
            return obj

        obj = cls(store=store)
        # Use setattr instead of passing it to the constructor, since not all
        # constructors accept all properties. There is no check if the
        # properties are valid since it will fail in the store.find() call above.
        for key, value in kwargs.items():
            setattr(obj, key, value)

        return obj

    @classmethod
    def validate_attr(cls, attr, expected_type=None):
        """Make sure attr belongs to cls and has the expected type

        :param attr: the attr we will check if it is on cls
        :param expected_type: the expected type for the attr to be
            an instance of. If ``None`` will default to Property
        :raises: :exc:`TypeError` if the attr is not an instance
            of expected_type
        :raises: :exc:`ValueError` if the attr does not belong to
            this class
        """
        expected_type = expected_type or Property
        if not issubclass(expected_type, Property):
            raise TypeError(
                "expected_type %s needs to be a %s subclass" % (
                    expected_type, Property))

        # We need to iterate over cls._storm_columns to find the
        # attr's property because there's no reference to that property
        # (the descriptor) on the attr
        for attr_property, column in cls._storm_columns.items():
            if column is attr:
                break
        else:
            attr_property = None  # pylint
            raise ValueError("Domain %s does not have a column %s" % (
                cls.__name__, attr.name))

        if not isinstance(attr_property, expected_type):
            raise TypeError("attr %s needs to be a %s instance" % (
                attr.name, expected_type))

    @classmethod
    def validate_batch(cls, batch, sellable, storable=None):
        """Verifies if the given |batch| is valid for the given |sellable|.

        :param batch: A |storablebatch| that is being validated
        :param sellable: A |sellable| that we should use to validate against the batch
        :param storable: If provided, the corresponding |storable| for the given
            batch, to avoid unecessary queries.
         """
        if not storable:
            product = sellable.product
            storable = product and product.storable or None

        if not batch:
            # When batch is not given, the only accepted scenarios are that storable is
            # None or the storable does not require batches
            if not storable or not storable.is_batch:
                return
            raise ValueError('Batch should not be None for %r' % sellable)

        # From now on, batch is not None
        if not storable:
            raise ValueError('Batches should only be used with storables, '
                             'but %r is not one' % sellable)
        if not storable.is_batch:
            raise ValueError('This storable %r does not require a batch' %
                             storable)
        if batch.storable != storable:
            raise ValueError('Given batch %r and storable %r are not related' %
                             (batch, storable))
