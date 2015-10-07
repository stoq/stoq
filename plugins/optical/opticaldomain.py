# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import collections
import decimal

from storm.expr import Join, LeftJoin, Coalesce, Sum, Eq
from storm.references import Reference

from stoqlib.database.expr import StatementTimestamp
from stoqlib.database.properties import (DecimalCol, DateTimeCol, EnumCol,
                                         UnicodeCol, IdCol, BoolCol)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.events import DomainMergeEvent
from stoqlib.domain.person import Person, Company, Branch
from stoqlib.domain.product import Product, StorableBatch, ProductManufacturer
from stoqlib.domain.sale import SaleItem, Sale
from stoqlib.domain.sellable import Sellable, SellableCategory
from stoqlib.domain.workorder import WorkOrder, WorkOrderItem
from stoqlib.lib.translation import stoqlib_gettext as _


class OpticalMedic(Domain):
    """Information about the Medic (Ophtamologist)"""

    __storm_table__ = 'optical_medic'

    person_id = IdCol(allow_none=False)
    person = Reference(person_id, 'Person.id')

    # TODO: Find out a better name for crm
    crm_number = UnicodeCol()

    #: If this medic is a partner of the store, ie, if they recomend clients to
    #: this store
    partner = BoolCol()

    #
    # IDescribable implementation
    #

    @classmethod
    def get_person_by_crm(cls, store, document):
        query = cls.crm_number == document

        tables = [Person,
                  Join(OpticalMedic, Person.id == OpticalMedic.person_id)]
        return store.using(*tables).find(Person, query).one()

    def get_description(self):
        return _('%s (upid: %s)') % (self.person.name, self.crm_number)

    @DomainMergeEvent.connect
    @classmethod
    def on_domain_merge(cls, obj, other):
        if type(obj) != Person:
            return
        this_facet = obj.store.find(cls, person=obj).one()
        other_facet = obj.store.find(cls, person=other).one()
        if not this_facet and not other_facet:
            return
        obj.merge_facet(this_facet, other_facet)
        return set([('optical_medic', 'person_id')])


class OpticalProduct(Domain):
    """Stores information about products sold by optical stores.

    There are 3 main types of products sold by optical stores:

    - Glass frames (without lenses)
    - Glass lenses
    - Contact lenses
    """
    __storm_table__ = 'optical_product'

    #: The frame of the glases (without lenses)
    TYPE_GLASS_FRAME = u'glass-frame'

    #: The glasses to be used with a frame
    TYPE_GLASS_LENSES = u'glass-lenses'

    #: Contact lenses
    TYPE_CONTACT_LENSES = u'contact-lenses'

    product_id = IdCol(allow_none=False)
    product = Reference(product_id, 'Product.id')

    # The type indicates what of the following fields should be edited.
    optical_type = EnumCol()

    #: If this product should be reserved automatically when added to the sale
    #: with work order
    auto_reserve = BoolCol(default=True)

    #
    # Glass frame details
    #

    #: The type of the frame (prescription or sunglasses)
    gf_glass_type = UnicodeCol()

    #: Size of the frame, accordingly to the manufacturer (may also be a string,
    #: for instance Large, one size fits all, etc..)
    gf_size = UnicodeCol()

    # The type of the lenses used in this frame. (for isntance: demo lens,
    # solar, polarized, mirrored)
    gf_lens_type = UnicodeCol()

    # Color of the frame, accordingly to the manufacturer specification
    gf_color = UnicodeCol()

    #
    # Glass lenses details
    #

    # Fotossensivel
    #: Type of the lenses photosensitivity (for instance: tints, sunsensors,
    #: transitions, etc...)
    gl_photosensitive = UnicodeCol()

    # Anti reflexo
    #: A description of the anti glare treatment the lenses have.
    gl_anti_glare = UnicodeCol()

    # Índice refração
    #: Decimal value describing the refraction index
    gl_refraction_index = DecimalCol()

    # Classificação
    #: lenses may be monofocal, bifocal or multifocal
    gl_classification = UnicodeCol()

    # Adição
    #: Free text describing the range of the possible additions.
    gl_addition = UnicodeCol()

    # Diametro
    # Free text describing the range of the possible diameters for the lens
    gl_diameter = UnicodeCol()

    # Altura
    #: Free text describing the height of the lens
    gl_height = UnicodeCol()

    # Disponibilidade
    #: Free text describint the avaiability of the lens (in what possible
    #: parameters they are avaiable. For instance: "-10,00 a -2,25 Cil -2,00"
    gl_availability = UnicodeCol()

    #
    # Contact lenses details
    #

    # Grau
    #: Degree of the lenses, a decimal from -30 to +30, in steps of +- 0.25
    cl_degree = DecimalCol()

    # Classificação
    #: Free text describing the classification of the lenses (solid, gel, etc..)
    cl_classification = UnicodeCol()

    # tipo lente
    #: The type of the lenses (monofocal, toric, etc..)
    cl_lens_type = UnicodeCol()

    # Descarte
    #: How often the lens should be discarded (anually, daily, etc..)
    cl_discard = UnicodeCol()

    # Adição
    #: Free text describing the addition of the lenses.
    cl_addition = UnicodeCol()

    # Cilindrico
    # XXX: I still need to verify if a decimal column is ok, or if there are
    # possible text values.
    #: Cylindrical value of the lenses.
    cl_cylindrical = DecimalCol()

    # Eixo
    # XXX: I still need to verify if a decimal column is ok, or if there are
    # possible text values.
    #: Axix  of the lenses.
    cl_axis = DecimalCol()

    #: Free text color description of the lens (for cosmetic use)
    cl_color = UnicodeCol()

    # Curvatura
    #: Free text description of the curvature. normaly a decimal, but may have
    #: textual descriptions
    cl_curvature = UnicodeCol()

    @classmethod
    def get_from_product(cls, product):
        return product.store.find(cls, product=product).one()


class OpticalWorkOrder(Domain):
    """This holds the necessary information to execute an work order for optical
    stores.

    This includes all the details present in the prescription.

    For reference:
    http://en.wikipedia.org/wiki/Eyeglass_prescription

    See http://en.wikipedia.org/wiki/Eyeglass_prescription#Abbreviations_and_terms
    for reference no the names used here.

    In some places, RE is used as a short for right eye, and LE for left eye
    """
    __storm_table__ = 'optical_work_order'

    #: Lens used in glasses
    LENS_TYPE_OPHTALMIC = u'ophtalmic'

    #: Contact lenses
    LENS_TYPE_CONTACT = u'contact'

    #: The frame for the lens is a closed ring
    FRAME_TYPE_CLOSED_RING = u'closed-ring'

    #: The frame uses a nylon string to hold the lenses.
    FRAME_TYPE_NYLON = u'nylon'

    #: The frame is made 3 pieces
    FRAME_TYPE_3_PIECES = u'3-pieces'

    lens_types = {
        LENS_TYPE_OPHTALMIC: _('Ophtalmic'),
        LENS_TYPE_CONTACT: _('Contact'),
    }

    frame_types = {
        # Translators: Aro fechado
        FRAME_TYPE_3_PIECES: _('Closed ring'),

        # Translators: Fio de nylon
        FRAME_TYPE_NYLON: _('Nylon String'),

        # Translators: 3 preças
        FRAME_TYPE_CLOSED_RING: _('3 pieces'),
    }

    work_order_id = IdCol(allow_none=False)
    work_order = Reference(work_order_id, 'WorkOrder.id')

    medic_id = IdCol()
    medic = Reference(medic_id, 'OpticalMedic.id')

    prescription_date = DateTimeCol()

    #: The name of the patient. Note that we already have the client of the work
    #: order, but the patient may be someone else (like the son, father,
    #: etc...). Just the name is enough
    patient = UnicodeCol()

    #: The type of the lens, Contact or Ophtalmic
    lens_type = EnumCol(default=LENS_TYPE_OPHTALMIC)

    #
    #   Frame
    #

    #: The type of the frame. One of OpticalWorkOrder.FRAME_TYPE_*
    frame_type = EnumCol(default=FRAME_TYPE_CLOSED_RING)

    #: The vertical frame measure
    frame_mva = DecimalCol(default=decimal.Decimal(0))

    #: The horizontal frame measure
    frame_mha = DecimalCol(default=decimal.Decimal(0))

    #: The diagonal frame measure
    frame_mda = DecimalCol(default=decimal.Decimal(0))

    #: The brige is the part of the frame between the two lenses, above the nose.
    frame_bridge = DecimalCol()

    #
    # Left eye distance vision
    #

    le_distance_spherical = DecimalCol(default=0)
    le_distance_cylindrical = DecimalCol(default=0)
    le_distance_axis = DecimalCol(default=0)
    le_distance_prism = DecimalCol(default=0)
    le_distance_base = DecimalCol(default=0)
    le_distance_height = DecimalCol(default=0)

    #: Pupil distance (DNP in pt_BR)
    le_distance_pd = DecimalCol(default=0)
    le_addition = DecimalCol(default=0)

    #
    # Left eye distance vision
    #
    le_near_spherical = DecimalCol(default=0)
    le_near_cylindrical = DecimalCol(default=0)
    le_near_axis = DecimalCol(default=0)

    #: Pupil distance (DNP in pt_BR)
    le_near_pd = DecimalCol(default=0)

    #
    # Right eye distance vision
    #

    re_distance_spherical = DecimalCol(default=0)
    re_distance_cylindrical = DecimalCol(default=0)
    re_distance_axis = DecimalCol(default=0)
    re_distance_prism = DecimalCol(default=0)
    re_distance_base = DecimalCol(default=0)
    re_distance_height = DecimalCol(default=0)

    #: Pupil distance (DNP in pt_BR)
    re_distance_pd = DecimalCol(default=0)
    re_addition = DecimalCol(default=0)

    #
    # Right eye near vision
    #
    re_near_spherical = DecimalCol(default=0)
    re_near_cylindrical = DecimalCol(default=0)
    re_near_axis = DecimalCol(default=0)

    #: Pupil distance (DNP in pt_BR)
    re_near_pd = DecimalCol(default=0)

    @property
    def frame_type_str(self):
        return self.frame_types.get(self.frame_type, '')

    @property
    def lens_type_str(self):
        return self.lens_types.get(self.lens_type, '')


class OpticalPatientHistory(Domain):

    __storm_table__ = 'optical_patient_history'

    #: Never used lenses before
    TYPE_FIRST_USER = u'first-user'

    #: Is currently a user
    TYPE_SECOND_USER = u'second-user'

    #: Has used lenses before, but stopped
    TYPE_EX_USER = u'ex-user'

    user_types = collections.OrderedDict([
        (TYPE_FIRST_USER, _('First User')),
        (TYPE_SECOND_USER, _('Second User')),
        (TYPE_EX_USER, _('Ex-User')),
    ])

    create_date = DateTimeCol(default_factory=StatementTimestamp)

    client_id = IdCol(allow_none=False)
    #: The related client
    client = Reference(client_id, 'Client.id')

    responsible_id = IdCol(allow_none=False)
    #: The user that registred this information
    responsible = Reference(responsible_id, 'LoginUser.id')

    #
    #   Section 1: General questions
    #

    #: If the patient is a first time user for contact lenses or not.
    user_type = EnumCol(allow_none=False, default=TYPE_FIRST_USER)

    #: What is the occupation of the patient
    occupation = UnicodeCol()

    #: Details about the work environment (if it as air conditioning, dust,
    #: chemical products)
    work_environment = UnicodeCol()

    #
    #   First time user
    #

    #: If the patient has ever tested any contact lenses
    has_tested = UnicodeCol()

    #: What brands the patient has tested
    tested_brand = UnicodeCol()

    #: If previous tests irritated the eye
    eye_irritation = UnicodeCol()

    #: What is the main purpose for using contact lenses?
    purpose_of_use = UnicodeCol()

    #: How many hours per day the patient intends to use the contact lenses
    intended_hour_usage = UnicodeCol()

    #
    #   Second time / ex user
    #

    #: Previous brand of the client.
    previous_brand = UnicodeCol()

    #: What the previous brand felt like
    previous_feeling = UnicodeCol()

    #: Have ever had any cornea issues
    cornea_issues = UnicodeCol()

    #: How many hours per day the client used the lenses
    hours_per_day_usage = UnicodeCol()

    #
    #   Second time user
    #

    #: For how long is a user
    user_since = UnicodeCol()

    #: Bring the previous lenses?
    has_previous_lenses = UnicodeCol()

    #: Previous lenses observations
    previous_lenses_notes = UnicodeCol()

    #
    #   Ex User
    #

    #: How long since the last use.
    last_use = UnicodeCol()

    #: why stopped using
    stop_reason = UnicodeCol()

    #: Did frequent removal of proteins?
    protein_removal = UnicodeCol()

    #: What cleaning product used?
    cleaning_product = UnicodeCol()

    #: Free notes.
    history_notes = UnicodeCol()

    #
    #   Section 2: Adaptation test
    #

    #: If the patient ever had eye injuries
    eye_injury = UnicodeCol()

    #: Any kind of recent pathology, like pink-eye
    recent_pathology = UnicodeCol()

    #: Is currently using eye drops
    using_eye_drops = UnicodeCol()

    #: Does the patient have health problems
    health_problems = UnicodeCol()

    #: Is the patient is using any kind of medicament
    using_medicament = UnicodeCol()

    #: Does the patient family has any health problems
    family_health_problems = UnicodeCol()

    #: How the eyes feel at the end of the day (burn, itch, etc...)
    end_of_day_feeling = UnicodeCol()

    #: Free notes.
    adaptation_notes = UnicodeCol()

    @property
    def responsible_name(self):
        return self.responsible.get_description()


class OpticalPatientMeasures(Domain):

    __storm_table__ = 'optical_patient_measures'

    EYE_LEFT = u'left'
    EYE_RIGHT = u'right'

    eye_options = {
        EYE_LEFT: _('Left Eye'),
        EYE_RIGHT: _('Right Eye'),
    }

    create_date = DateTimeCol(default_factory=StatementTimestamp)

    client_id = IdCol(allow_none=False)
    #: The related client
    client = Reference(client_id, 'Client.id')

    responsible_id = IdCol(allow_none=False)
    #: The user that registred this information
    responsible = Reference(responsible_id, 'LoginUser.id')

    dominant_eye = EnumCol(allow_none=False, default=EYE_LEFT)

    le_keratometer_horizontal = UnicodeCol()
    le_keratometer_vertical = UnicodeCol()
    le_keratometer_axis = UnicodeCol()

    re_keratometer_horizontal = UnicodeCol()
    re_keratometer_vertical = UnicodeCol()
    re_keratometer_axis = UnicodeCol()

    le_eyebrown = UnicodeCol()
    le_eyelash = UnicodeCol()
    le_conjunctiva = UnicodeCol()
    le_sclerotic = UnicodeCol()
    le_iris_diameter = UnicodeCol()
    le_eyelid = UnicodeCol()
    le_eyelid_opening = UnicodeCol()
    le_cornea = UnicodeCol()
    #: Tear breakup time. How much time the eye takes to produce a tear
    le_tbut = UnicodeCol()

    #: test that checks how much tear the eye produces
    le_schirmer = UnicodeCol()

    re_eyebrown = UnicodeCol()
    re_eyelash = UnicodeCol()
    re_conjunctiva = UnicodeCol()
    re_sclerotic = UnicodeCol()
    re_iris_diameter = UnicodeCol()
    re_eyelid = UnicodeCol()
    re_eyelid_opening = UnicodeCol()
    re_cornea = UnicodeCol()

    #: Tear breakup time. How much time the eye takes to produce a tear
    re_tbut = UnicodeCol()

    #: test that checks how much tear the eye produces
    re_schirmer = UnicodeCol()

    notes = UnicodeCol()

    @property
    def responsible_name(self):
        return self.responsible.get_description()


class OpticalPatientTest(Domain):
    __storm_table__ = 'optical_patient_test'

    create_date = DateTimeCol(default_factory=StatementTimestamp)

    client_id = IdCol(allow_none=False)
    #: The related client
    client = Reference(client_id, 'Client.id')

    responsible_id = IdCol(allow_none=False)
    #: The user that registred this information
    responsible = Reference(responsible_id, 'LoginUser.id')

    #: The contact lens that is being tested. This could be a reference to a
    #: |product in the future
    le_item = UnicodeCol()

    #: The brand of the tested contact lenses
    le_brand = UnicodeCol()

    #: Curva Base - CB
    le_base_curve = UnicodeCol()

    le_spherical_degree = UnicodeCol()
    le_cylindrical = UnicodeCol()
    le_axis = UnicodeCol()
    le_diameter = UnicodeCol()
    le_movement = UnicodeCol()
    le_centralization = UnicodeCol()
    le_spin = UnicodeCol()
    le_fluorescein = UnicodeCol()

    #: Sobre refração - SRF
    le_over_refraction = UnicodeCol()
    le_bichrome = UnicodeCol()

    #: If the client is satisfied with this product
    le_client_approved = BoolCol()

    #: If the client has purchased this product after the test.
    le_client_purchased = BoolCol()

    #: If the product being tested was delivered to the client
    le_delivered = BoolCol()

    re_item = UnicodeCol()
    re_brand = UnicodeCol()
    re_base_curve = UnicodeCol()
    re_spherical_degree = UnicodeCol()
    re_cylindrical = UnicodeCol()
    re_axis = UnicodeCol()
    re_diameter = UnicodeCol()
    re_movement = UnicodeCol()
    re_centralization = UnicodeCol()
    re_spin = UnicodeCol()
    re_fluorescein = UnicodeCol()
    re_over_refraction = UnicodeCol()
    re_bichrome = UnicodeCol()
    re_client_approved = BoolCol()
    re_client_purchased = BoolCol()
    re_delivered = BoolCol()

    #: Free notes
    notes = UnicodeCol()

    @property
    def responsible_name(self):
        return self.responsible.get_description()


class OpticalPatientVisualAcuity(Domain):
    __storm_table__ = 'optical_patient_visual_acuity'

    create_date = DateTimeCol(default_factory=StatementTimestamp)

    client_id = IdCol(allow_none=False)
    #: The related client
    client = Reference(client_id, 'Client.id')

    responsible_id = IdCol(allow_none=False)
    #: The user that registred this information
    responsible = Reference(responsible_id, 'LoginUser.id')

    be_distance_glasses = UnicodeCol()
    le_distance_glasses = UnicodeCol()
    re_distance_glasses = UnicodeCol()

    be_distance_lenses = UnicodeCol()
    le_distance_lenses = UnicodeCol()
    re_distance_lenses = UnicodeCol()

    be_near_glasses = UnicodeCol()
    be_near_lenses = UnicodeCol()

    #: Free notes
    notes = UnicodeCol()

    @property
    def responsible_name(self):
        return self.responsible.get_description()


class OpticalMedicView(Viewable):
    medic = OpticalMedic

    id = Person.id
    name = Person.name
    crm_number = OpticalMedic.crm_number
    partner = OpticalMedic.partner
    phone_number = Person.phone_number

    tables = [
        Person,
        Join(OpticalMedic, Person.id == OpticalMedic.person_id)
    ]

    clause = Eq(Person.merged_with_id, None)


class MedicSoldItemsView(Viewable):
    branch = Branch

    id = Sellable.id
    identifier = Sale.identifier
    code = Sellable.code
    description = Sellable.description
    category = SellableCategory.description
    manufacturer = ProductManufacturer.name
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date
    sale_id = Sale.id
    open_date = Sale.open_date
    confirm_date = Sale.confirm_date

    branch_name = Company.fancy_name
    medic_name = Person.name
    crm_number = OpticalMedic.crm_number
    partner = OpticalMedic.partner

    quantity = Sum(SaleItem.quantity)
    total = Sum(SaleItem.quantity * SaleItem.price)

    tables = [
        Sellable,
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
        Join(SaleItem, SaleItem.sellable_id == Sellable.id),
        Join(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(StorableBatch, StorableBatch.id == SaleItem.batch_id),
        Join(Branch, Sale.branch_id == Branch.id),
        Join(Company, Branch.person_id == Company.person_id),
        Join(WorkOrderItem, WorkOrderItem.sale_item_id == SaleItem.id),
        Join(WorkOrder, WorkOrder.id == WorkOrderItem.order_id),
        Join(OpticalWorkOrder, OpticalWorkOrder.work_order_id == WorkOrder.id),
        Join(OpticalMedic, OpticalMedic.id == OpticalWorkOrder.medic_id),
        Join(Person, Person.id == OpticalMedic.person_id),
    ]

    clause = Sale.status == Sale.STATUS_CONFIRMED

    group_by = [id, branch_name, code, description, category, manufacturer,
                StorableBatch.id, OpticalMedic.id, Person.id, Sale.id, Branch.id]
