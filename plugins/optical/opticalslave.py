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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Slaves for optical stores """

import gtk

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.translation import stoqlib_gettext

from optical.opticaldomain import OpticalWorkOrder, OpticalProduct

_ = stoqlib_gettext


# FIXME: Implement this completely:
# - Improve interface
class ProductOpticSlave(BaseEditorSlave):
    gladefile = 'ProductOpticSlave'
    title = _(u'Optic Details')
    model_type = object
    glass_widgets = ['gf_glass_type', 'gf_size', 'gf_lens_type', 'gf_color']
    glass_lens_widgets = ['gl_photosensitive', 'gl_anti_glare',
                          'gl_refraction_index', 'gl_classification',
                          'gl_addition', 'gl_diameter', 'gl_height',
                          'gl_availability']
    contact_lens_widgets = ['cl_degree', 'cl_classification', 'cl_lens_type',
                            'cl_discard', 'cl_addition', 'cl_cylindrical',
                            'cl_axis', 'cl_color', 'cl_curvature']
    proxy_widgets = (['optical_type'] + glass_widgets + glass_lens_widgets +
                     contact_lens_widgets)

    def __init__(self, store, product, model=None):
        self._product = product
        BaseEditorSlave.__init__(self, store, model)

    def create_model(self, store):
        model = store.find(OpticalProduct, product=self._product).one()
        if model is None:
            model = OpticalProduct(product=self._product, store=store)
        return model

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductOpticSlave.proxy_widgets)

    def _toggle_details_type(self, optical_type):
        self.gf_details.set_visible(optical_type == OpticalProduct.TYPE_GLASS_FRAME)
        self.gl_details.set_visible(optical_type == OpticalProduct.TYPE_GLASS_LENSES)
        self.cl_details.set_visible(optical_type == OpticalProduct.TYPE_CONTACT_LENSES)

    def _setup_widgets(self):
        self.optical_type.prefill([
            (_('None'), None),
            (_('Glasses'), OpticalProduct.TYPE_GLASS_FRAME),
            # Translators: Lente Oftálmica
            (_('Glass Lenses'), OpticalProduct.TYPE_GLASS_LENSES),
            # Translators: Lente de Contato
            (_('Contact Lenses'), OpticalProduct.TYPE_CONTACT_LENSES),
        ])
        self._toggle_details_type(self.model.optical_type)

    def on_optical_type__changed(self, widget):
        self._toggle_details_type(widget.get_selected_data())


class WorkOrderOpticalSlave(BaseEditorSlave):
    """This slave edits the optical information needed by a given workorder.
    """
    gladefile = 'WorkOrderOpticalSlave'
    title = _(u'Optical Details')
    model_type = object
    proxy_widgets = ['prescription_date', 'patient', 'lens_type', 'frame_type']
    workorder_widgets = ['estimated_finish']

    # This is a dictionary of specifications for each widget in the slave. each item
    # in this dict should be a touple that defines the following:
    #   - Minimum allowed value
    #   - Maximum allowed value
    #   - Number of decimal places that should be used
    #   - Step increment for the adjustment
    #   - Page increment for the adjustment
    # The key shoud be the name of the widget (There are actually 2 widgets, one
    # for each eye)
    optical_widgets = {
        'distance_spherical': (-30, 30, 2, 0.25, 1),
        'distance_cylindrical': (-10, 10, 2, 0.25, 1),
        'distance_axis': (0, 180, 0, 1, 10),
        'distance_pd': (22, 40, 1, 0.1, 1),
        'distance_prism': (0, 10, 2, 0.25, 1),
        'distance_base': (0, 10, 2, 0.25, 1),
        'distance_height': (10, 30, 2, 0.25, 1),
        'addition': (0, 4, 2, 0.25, 1),
        'near_spherical': (-30, 30, 2, 0.25, 1),
        'near_cylindrical': (-10, 10, 2, 0.25, 1),
        'near_axis': (0, 180, 0, 1, 10),
        'near_pd': (22, 40, 1, 0.1, 1),
    }

    frame_widgets = {
        'frame_mva': (10, 40, 1, 0.1, 1),
        'frame_mha': (40, 70, 1, 0.1, 1),
        'frame_bridge': (5, 25, 1, 0.1, 1),
    }

    def __init__(self, store, workorder, show_finish_date=False):
        """
        :param workorder: The |workorder| this slave is editing. We will
          actually edit another object, but the |workorder| will be used to
          fetch or create it.
        :param show_finish_date: If the estimated finish date property of the
          work order should be editable in this slave.
        """
        self._show_finish_date = show_finish_date
        self._workorder = workorder
        model = self._create_model(store)
        BaseEditorSlave.__init__(self, store, model)

    def _create_model(self, store):
        model = store.find(OpticalWorkOrder,
                           work_order=self._workorder).one()
        if model is None:
            model = OpticalWorkOrder(work_order=self._workorder, store=store)
        return model

    def _setup_widgets(self):
        self.lens_type.prefill([
            (_('Ophtalmic'), OpticalWorkOrder.LENS_TYPE_OPHTALMIC),
            (_('Contact'), OpticalWorkOrder.LENS_TYPE_CONTACT),
        ])
        self.frame_type.prefill([
            (_('Acetate'), OpticalWorkOrder.FRAME_TYPE_ACETATE),
            (_('Nylon String'), OpticalWorkOrder.FRAME_TYPE_NYLON),
            (_('Metal'), OpticalWorkOrder.FRAME_TYPE_METAL),
        ])

    def _setup_adjustments(self):
        """This will setup the adjustments for the prescription widgets, and
        will return a list with all widget names, so they can be added to the
        proxy later.
        """
        widget_names = []
        for eye in ['le', 're']:
            for element in self.optical_widgets:
                name = eye + '_' + element
                widget_names.append(name)
                widget = getattr(self, name)

                lower, upper, digits, step, page = self.optical_widgets[element]
                widget.set_adjustment(gtk.Adjustment(lower=lower, upper=upper,
                                                     step_incr=step, page_incr=page))
                widget.set_digits(digits)

        for name in self.frame_widgets:
            widget_names.append(name)
            widget = getattr(self, name)

            lower, upper, digits, step, page = self.frame_widgets[name]
            widget.set_adjustment(gtk.Adjustment(lower=lower, upper=upper,
                                                 step_incr=step, page_incr=page))
            widget.set_digits(digits)

        return widget_names

    def setup_proxies(self):
        self._setup_widgets()
        adjustment_widgets = self._setup_adjustments()
        self.add_proxy(self.model, self.proxy_widgets + adjustment_widgets)

        # Finish date should only be visible if we are creating a new workorder
        # from the sale wizard
        if self._show_finish_date:
            self.add_proxy(self._workorder, self.workorder_widgets)
        else:
            self.estimated_finish_lbl.hide()
            self.estimated_finish.hide()

    #
    #   Callbacks
    #
    def on_lens_type__changed(self, widget):
        has_frame = self.model.lens_type == OpticalWorkOrder.LENS_TYPE_OPHTALMIC
        self.frame_box.set_sensitive(has_frame)
