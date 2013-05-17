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

from storm.references import Reference

from stoqlib.database.properties import IntCol, DecimalCol, DateTimeCol, UnicodeCol
from stoqlib.domain.base import Domain


class OpticalProduct(Domain):
    """Stores information about products sold by optical stores.

    There are 3 main types of products sold by optical stores:

    - Glass frames (without lenses)
    - Glass lenses
    - Contact lenses
    """
    __storm_table__ = 'optical_product'

    #: The frame of the glases (without lenses)
    TYPE_GLASS_FRAME = 0

    #: The glasses to be used with a frame
    TYPE_GLASS_LENSES = 1

    #: Contact lenses
    TYPE_CONTACT_LENSES = 2

    product_id = IntCol()
    product = Reference(product_id, 'Product.id')

    # The type indicates what of the following fields should be edited.
    optical_type = IntCol()

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

    work_order_id = IntCol()
    work_order = Reference(work_order_id, 'WorkOrder.id')

    prescription_date = DateTimeCol()
    # TODO: Create a 'physician' record and reference it here.

    #: The name of the patient. Note that we already have the client of the work
    #: order, but the patient may be someone else (like the son, father,
    #: etc...). Just the name is enough
    patient = UnicodeCol()

    #
    # Left eye distance vision
    #

    le_distance_spherical = DecimalCol()
    le_distance_cylindrical = DecimalCol()
    le_distance_axis = DecimalCol()
    le_distance_prism = DecimalCol()
    le_distance_base = DecimalCol()
    le_distance_height = DecimalCol()

    #: Pupil distance (DNP in pt_BR)
    le_distance_pd = DecimalCol()
    le_addition = DecimalCol()

    #
    # Left eye distance vision
    #
    le_near_spherical = DecimalCol()
    le_near_cylindrical = DecimalCol()
    le_near_axis = DecimalCol()

    #: Pupil distance (DNP in pt_BR)
    le_near_pd = DecimalCol()

    #
    # Right eye distance vision
    #

    re_distance_spherical = DecimalCol()
    re_distance_cylindrical = DecimalCol()
    re_distance_axis = DecimalCol()
    re_distance_prism = DecimalCol()
    re_distance_base = DecimalCol()
    re_distance_height = DecimalCol()

    #: Pupil distance (DNP in pt_BR)
    re_distance_pd = DecimalCol()
    re_addition = DecimalCol()

    #
    # Right eye near vision
    #
    re_near_spherical = DecimalCol()
    re_near_cylindrical = DecimalCol()
    re_near_axis = DecimalCol()

    #: Pupil distance (DNP in pt_BR)
    re_near_pd = DecimalCol()
