# -*- coding: utf-8 -*-
from storm.references import Reference

from stoqlib.database.orm import UnicodeCol, BoolCol, IntCol
from stoqlib.lib.translation import N_
from stoqlib.migration.domainv1 import Domain


class UIForm(Domain):
    __storm_table__ = 'ui_form'

    form_name = UnicodeCol()
    description = UnicodeCol()

    def get_field(self, field_name):
        store = self.store
        return store.find(UIField, field_name=field_name, ui_form=self).one()


class UIField(Domain):
    __storm_table__ = 'ui_field'

    ui_form_id = IntCol()
    ui_form = Reference(ui_form_id, UIForm.id)
    field_name = UnicodeCol()
    description = UnicodeCol()
    visible = BoolCol()
    mandatory = BoolCol()


def _add_fields_to_form(store, ui_form, fields):
    for (field_name, field_description,
         visible, mandatory) in fields:
        ui_field = store.find(UIField, ui_form=ui_form,
                              field_name=field_name).one()
        if ui_field is not None:
            continue

        UIField(store=store,
                ui_form=ui_form,
                field_name=field_name,
                description=field_description,
                visible=visible,
                mandatory=mandatory)


def _get_or_create_form(store, name, desc):
    ui_form = store.find(UIForm, form_name=name).one()
    if ui_form is None:
        ui_form = UIForm(store=store, form_name=name, description=desc)
    return ui_form


def create_default_forms(store):
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
        ('genero', N_(u'Mercosul Gênero'), True, False),
    ]
    for name, desc in [('user', N_('User')),
                       ('client', N_('Client')),
                       ('employee', N_('Employee')),
                       ('supplier', N_('Supplier')),
                       ('transporter', N_('Transporter')),
                       ('branch', N_('Branch'))]:
        ui_form = _get_or_create_form(store, name, desc)
        _add_fields_to_form(store, ui_form, person_fields)

    employee_form = store.find(UIForm, form_name='employee').one()
    _add_fields_to_form(store, employee_form, employee_fields)

    product_form = _get_or_create_form(store, 'product', N_('Product'))
    _add_fields_to_form(store, product_form, product_fields)


def apply_patch(store):
    store.execute("""
CREATE TABLE ui_form (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    form_name text UNIQUE
);

CREATE TABLE ui_field (
    id serial NOT NULL PRIMARY KEY,
    te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
    te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
    description text,
    field_name text,
    mandatory boolean,
    visible boolean,
    ui_form_id bigint REFERENCES ui_form(id)
);""")

    create_default_forms(store)
