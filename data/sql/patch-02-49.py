# -*- coding: utf-8 -*-
from storm.references import Reference

from stoqlib.database.properties import UnicodeCol, BoolCol, IntCol
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
        (u'name', N_(u'Name'), True, True),
        (u'phone_number', N_(u'Phone number'), True, False),
        (u'mobile_number', N_(u'Mobile number'), True, False),
        (u'fax', N_(u'Fax'), True, False),
        (u'email', N_(u'Email'), True, False),
        (u'street', N_(u'Street'), True, True),
        (u'street_number', N_(u'Street number'), True, True),
        (u'postal_code', N_(u'Postal code'), True, False),
        (u'district', N_(u'District'), True, True),
        (u'complement', N_(u'Complement'), True, False),
        (u'city', N_(u'City'), True, False),
        (u'state', N_(u'State'), True, True),
        (u'country', N_(u'Country'), True, True),
    ]

    employee_fields = [
        (u'role', N_(u'Role'), True, True),
        (u'salary', N_(u'Salary'), True, True),
    ]

    product_fields = [
        (u'code', N_(u'Code'), True, False),
        (u'barcode', N_(u'Barcode'), True, False),
        (u'category', N_(u'Category'), True, False),
        (u'location', N_(u'Location'), True, False),
        (u'part_number', N_(u'Part number'), True, False),
        (u'width', N_(u'Width'), True, False),
        (u'height', N_(u'Height'), True, False),
        (u'depth', N_(u'Depth'), True, False),
        (u'weight', N_(u'Weight'), True, False),
        (u'minimum_quantity', N_(u'Minimum quantity'), True, False),
        (u'maximum_quantity', N_(u'Maximum quantity'), True, False),
        (u'manufacturer', N_(u'Manufacturer'), True, False),
        (u'ncm', N_(u'Mercosul NCM'), True, False),
        (u'ex_tipi', N_(u'Mercosul EX Tipi'), True, False),
        (u'genero', N_(u'Mercosul Gênero'), True, False),
    ]
    for name, desc in [(u'user', N_(u'User')),
                       (u'client', N_(u'Client')),
                       (u'employee', N_(u'Employee')),
                       (u'supplier', N_(u'Supplier')),
                       (u'transporter', N_(u'Transporter')),
                       (u'branch', N_(u'Branch'))]:
        ui_form = _get_or_create_form(store, name, desc)
        _add_fields_to_form(store, ui_form, person_fields)

    employee_form = store.find(UIForm, form_name=u'employee').one()
    _add_fields_to_form(store, employee_form, employee_fields)

    product_form = _get_or_create_form(store, u'product', N_(u'Product'))
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
