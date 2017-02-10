# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2017 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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

from decimal import Decimal

from kiwi.python import strip_accents

from stoqlib.lib.dateutils import localnow


class Field(object):
    """A field in an CNAB Record.

    :param name: the name of the field, used internally.
    :param size: the length of the field.
    :param type: the type of the field. One of: int, str or Decimal.
    :param default_value: The default value of the field. If None, then the
      field is mandatory
    :param decimals: When the value is of type Decimal, then this will be added
      to the length, and the number will be formated accordingly.
    """

    def __init__(self, name, type, size, default_value=None, decimals=2):
        self.name = name
        self.type = type
        self.decimals = decimals
        self.size = size
        if type is Decimal:
            self.size += self.decimals

        # Save default value separately, since it has a lower precedence
        self.default_value = default_value
        self.value = None

    def get_value(self):
        """Gets the value of this field.

        The order that the value is feched is:

            1 - First, the value set by calling set_value.
            2 - If set_value was not called, then the record this fields
                belongs to is asked for the value.
            3 - If the record does not have a value, then the default value is returned
        """
        if self.name in ('cnab', '_'):
            return None

        if self.value is not None:
            return self.value
        record_value = self.record.get_value(self.name)
        if record_value is not None:
            return record_value
        return self.default_value

    def set_value(self, value):
        """Sets the value for this field"""
        self.value = value

    def set_record(self, record):
        """Sets the record this field belongs to

        :param record: An instance of `Record`
        """
        self.record = record

    def as_string(self):
        """Formats this field to its string representation"""
        value = self.get_value()
        # cnab fields are always None
        if self.name not in ['cnab', '_']:
            assert value is not None, self.name

        if self.type is str:
            value = strip_accents(str(value or '')).ljust(self.size)[:self.size]
        elif self.type is int:
            value = str(value or 0).rjust(self.size, '0')
            assert len(value) == self.size, (self.name, value, len(value), self.size)
        elif self.type is Decimal:
            value = value or 0
            value = str(int(value * (10 ** self.decimals)))
            value = str(value).rjust(self.size, '0')
            assert len(value) == self.size, (value, len(value), self.size)

        return value or ''


class Record(object):
    """A record in a CNAB file.

    A record is a single line in the CNAB, and is composed of a series of
    fields.
    """

    #: The expected size for this record.
    size = 240

    #: A list of `Field` objects
    fields = []

    #: spec defining fields that should be replaced by other fields.
    replace_fields = {}

    def __init__(self, **kwargs):
        # Build a new private fields list based on fields and replace fields to
        # avoid the class fields definition being overwriten by the replace
        # fields bellow
        self._fields = []
        field_map = {}
        for field in self.fields:
            field.set_record(self)
            field_map[field.name] = field
            self._fields.append(field)

        # Replace fields
        for key, new_values in self.replace_fields.items():
            pos = self._fields.index(field_map[key])
            self._fields.pop(pos)
            for field in reversed(new_values):
                field.set_record(self)
                self._fields.insert(pos, field)
                field_map[field.name] = field

        # Validate the size
        size = sum(field.size for field in self._fields)
        assert size == self.size, (self, size)

        for key, value in kwargs.items():
            field = field_map[key]
            field.set_value(value)

    def get_value(self, name):
        """Gets a value for a given field name

        If this record does not have a value for this field, the parent bank
        cnab specification will be checked
        """
        if hasattr(self, name):
            return getattr(self, name)

        return self.cnab.get_value(name)

    def set_cnab(self, cnab):
        """Set the parent cnab specification this record belongs to

        :param cnab: an instance of `Cnab`
        """
        self.cnab = cnab

    def as_string(self):
        value = ''.join(f.as_string() for f in self._fields)
        assert len(value) == self.size, (len(value), self.size)
        return value


class Cnab(object):

    def __init__(self, branch, bank, bank_info):
        self.bank_info = bank_info
        self.records = []
        person = branch.person
        company = branch.person.company
        raw_document = ''.join(i for i in company.cnpj if i.isdigit())
        now = localnow()

        self.default_values = dict(
            company_document=raw_document,
            company_name=person.name,
            # now
            create_date=now.strftime('%d%m%Y'),
            create_time=now.strftime('%H%M'),
            # account
            agency=bank_info.agencia.split('-')[0],
            agency_dv=bank_info.dv_agencia,
            account=bank_info.conta.split('-')[0],
            account_dv=bank_info.dv_conta,
        )
        for opt in bank.options:
            self.default_values[opt.option] = opt.value

    def get_value(self, field):
        """Gets a value for a given field name

        If this spec does not this named field, an AttributeError will be
        raised.
        """
        if hasattr(self, field):
            return getattr(self, field)
        if field in self.default_values:
            return self.default_values[field]
        if hasattr(self.bank_info, field):
            return getattr(self.bank_info, field)
        return None

    def add_record(self, record_type, *args, **kwargs):
        """Adds a record to this cnab spec"""
        record = record_type(*args, **kwargs)
        record.set_cnab(self)
        self.records.append(record)
        return record

    def as_string(self):
        # Cnab requires an extra \r\n at the last line
        return '\r\n'.join(r.as_string() for r in self.records) + '\r\n'

    def __repr__(self):  # pragma no cover
        return '<{} records={}>'.format(self.__class__.__name__, len(self.records))
