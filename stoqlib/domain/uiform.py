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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
""" Domain classes to define required and visible fields """

from stoqlib.database.orm import ForeignKey, BoolCol, UnicodeCol
from stoqlib.database.orm import SingleJoin
from stoqlib.domain.base import Domain
from stoqlib.lib.translation import stoqlib_gettext, N_

_ = stoqlib_gettext


class UIField(Domain):
    """This describes a field in form a.
    Can be used makae fields mandatory or hide them completely.
    """
    ui_form = ForeignKey('UIForm')
    field_name = UnicodeCol()
    description = UnicodeCol()
    visible = BoolCol()
    mandatory = BoolCol()


class UIForm(Domain):
    """This describes a form which has a number of fields"""
    form_name = UnicodeCol()
    description = UnicodeCol()
    fields = SingleJoin('UIField')

    def get_field(self, field_name):
        return UIField.selectOneBy(field_name=field_name,
                                   ui_form=self,
                                   connection=self.get_connection())


def _add_fields_to_form(trans, ui_form, fields):
    for (field_name, field_description,
         visible, mandatory) in fields:
        ui_field = UIField.selectOneBy(connection=trans,
                                       ui_form=ui_form,
                                       field_name=field_name)
        if ui_field is not None:
            continue
        UIField(connection=trans,
                ui_form=ui_form,
                field_name=field_name,
                description=field_description,
                visible=visible,
                mandatory=mandatory)


def _get_or_create_form(trans, name, desc):
    ui_form = UIForm.selectOneBy(connection=trans,
                                 form_name=name)
    if ui_form is None:
        ui_form = UIForm(connection=trans,
                         form_name=name,
                         description=desc)
    return ui_form


def create_default_forms(trans):
    person_fields = [
        ('name', N_('Name'), True, True),
        ('phone_number', N_('Phone number'), True, False),
        ('mobile_number', N_('Mobile number'), True, False),
        ('fax', N_('Fax'), True, False),
        ('email', N_('Email'), True, False),
        ('street', N_('Street'), True, True),
        ('street_number', N_('Street number'), True, True),
        ('postal_code', N_('Postal code'), True, False),
        ('district', N_('District'), True, True),
        ('complement', N_('Complement'), True, False),
        ('city', N_('City'), True, False),
        ('state', N_('State'), True, True),
        ('country', N_('Country'), True, True),
        ]

    employee_fields = [
        ('role', N_('Role'), True, True),
        ('salary', N_('Salary'), True, True),
        ]

    product_fields = [
        ('code', N_('Code'), True, False),
        ('barcode', N_('Barcode'), True, False),
        ('category', N_('Category'), True, False),
        ('location', N_('Location'), True, False),
        ('part_number', N_('Part number'), True, False),
        ('width', N_('Width'), True, False),
        ('height', N_('Height'), True, False),
        ('depth', N_('Depth'), True, False),
        ('weight', N_('Weight'), True, False),
        ('minimum_quantity', N_('Minimum quantity'), True, False),
        ('maximum_quantity', N_('Maximum quantity'), True, False),
        ('manufacturer', N_('Manufacturer'), True, False),
        ('ncm', N_('Mercosul NCM'), True, False),
        ('ex_tipi', N_('Mercosul EX Tipi'), True, False),
        ('genero', N_('Mercosul Gênero'), True, False),
    ]
    for name, desc in [('user', N_('User')),
                       ('client', N_('Client')),
                       ('employee', N_('Employee')),
                       ('supplier', N_('Supplier')),
                       ('transporter', N_('Transporter')),
                       ('branch', N_('Branch'))]:
        ui_form = _get_or_create_form(trans, name, desc)
        _add_fields_to_form(trans, ui_form, person_fields)

    employee_form = UIForm.selectOneBy(connection=trans,
                                       form_name='employee')
    _add_fields_to_form(trans, employee_form, employee_fields)

    product_form = _get_or_create_form(trans, 'product', N_('Product'))
    _add_fields_to_form(trans, product_form, product_fields)
