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

from decimal import Decimal

import gtk
from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext

from .opticaldomain import OpticalWorkOrder, OpticalProduct, OpticalMedic
from .opticaleditor import MedicEditor
_ = stoqlib_gettext

#: Number of days that we will consider the prescription to be old, and warn the
#: user. This is not a validation, but just a warning. This could also be a
#: parameter
LATE_PRESCRIPTION_DAYS = 365


class MedicDetailsSlave(BaseEditorSlave):
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'MedicDetailsSlave'
    title = _(u'Medic Details')
    model_type = object
    proxy_widgets = ['crm_number', 'partner']

    def __init__(self, store, medic, model=None, visual_mode=False):
        self._medic = medic
        BaseEditorSlave.__init__(self, store, model, visual_mode=visual_mode)

    def create_model(self, store):
        return store.find(OpticalMedic, person=self._medic.person).one()

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, MedicDetailsSlave.proxy_widgets)

    #
    # Kiwi Callbacks
    #

    def on_crm_number__validate(self, entry, value):
        if self.model.check_unique_value_exists(attribute=OpticalMedic.crm_number,
                                                value=value):
            return ValidationError(u"This CRM number is already in use.")


# FIXME: Implement this completely:
# - Improve interface
class ProductOpticSlave(BaseEditorSlave):
    translation_domain = 'stoq'
    domain = 'optical'
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
    proxy_widgets = (['optical_type', 'auto_reserve'] + glass_widgets +
                     glass_lens_widgets + contact_lens_widgets)

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

        self.cl_axis.set_adjustment(gtk.Adjustment(0, 0, 180, 1, 10))
        self.cl_cylindrical.set_adjustment(gtk.Adjustment(0, -10, 10,
                                                          Decimal('0.25'), 1))
        self.cl_degree.set_adjustment(gtk.Adjustment(0, -30, 30,
                                                     Decimal('0.25'), 1))
        self.gl_refraction_index.set_adjustment(gtk.Adjustment(0, 0, 2,
                                                               Decimal('0.1'),
                                                               Decimal('0.5')))

    def on_optical_type__changed(self, widget):
        self._toggle_details_type(widget.get_selected_data())


class WorkOrderOpticalSlave(BaseEditorSlave):
    """This slave edits the optical information needed by a given workorder.
    """
    translation_domain = 'stoq'
    domain = 'optical'
    gladefile = 'WorkOrderOpticalSlave'
    title = _(u'Optical Details')
    model_type = object
    optical_wo_widgets = ['prescription_date', 'patient', 'lens_type',
                          'frame_type', 'medic_combo']
    workorder_widgets = ['estimated_finish']
    proxy_widgets = optical_wo_widgets + workorder_widgets

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
        'distance_spherical': (-30, 30, 2, Decimal('0.25'), 1),
        'distance_cylindrical': (-10, 10, 2, Decimal('0.25'), 1),
        'distance_axis': (0, 180, 0, 1, 10),
        'distance_pd': (22, 40, 1, Decimal('0.5'), 1),
        'distance_prism': (0, 10, 2, Decimal('0.25'), 1),
        'distance_base': (0, 10, 2, Decimal('0.25'), 1),
        'distance_height': (10, 40, 2, Decimal('0.5'), 1),
        'addition': (0, 4, 2, Decimal('0.25'), 1),
        'near_spherical': (-30, 30, 2, Decimal('0.25'), 1),
        'near_cylindrical': (-10, 10, 2, Decimal('0.25'), 1),
        'near_axis': (0, 180, 0, 1, 10),
        'near_pd': (22, 40, 1, Decimal('0.1'), 1),
    }

    frame_widgets = {
        'frame_mva': (10, 70, 1, Decimal('0.1'), 1),
        'frame_mha': (40, 80, 1, Decimal('0.1'), 1),
        'frame_mda': (10, 65, 1, Decimal('0.1'), 1),
        'frame_bridge': (5, 30, 1, Decimal('0.1'), 1),
    }

    def __init__(self, store, workorder, show_finish_date=False,
                 visual_mode=False, description=u""):
        """
        :param workorder: The |workorder| this slave is editing. We will
          actually edit another object, but the |workorder| will be used to
          fetch or create it.
        :param show_finish_date: If the estimated finish date property of the
          work order should be editable in this slave.
        """
        self._update_level = 0
        self._focus_change = False
        self._show_finish_date = show_finish_date
        self._workorder = workorder
        self._description = description
        model = self._create_model(store)

        # This is used to correctly triangulate the values of the spherical
        # widgets
        self._update_order = {'re': [], 'le': []}
        BaseEditorSlave.__init__(self, store, model, visual_mode=visual_mode)

    def _create_model(self, store):
        model = store.find(OpticalWorkOrder,
                           work_order=self._workorder).one()
        if model is None:
            model = OpticalWorkOrder(work_order=self._workorder, store=store,
                                     patient=self._description)
        return model

    def _setup_widgets(self):
        lens_types = [(value, key) for
                      key, value in OpticalWorkOrder.lens_types.items()]
        frame_types = [(value, key) for
                       key, value in OpticalWorkOrder.frame_types.items()]
        self.lens_type.prefill(sorted(lens_types))
        self.frame_type.prefill(sorted(frame_types))
        self._medic_combo_prefill()

    def _setup_adjustments(self):
        """This will setup the adjustments for the prescription widgets, and
        will return a list with all widget names, so they can be added to the
        proxy later.
        """
        widget_names = []

        def _setup_widget(name, lower, upper, digits, steps, page):
            widget = getattr(self, name)
            widget_names.append(name)
            widget.set_digits(digits)

            # If the minimum value is greater than 0, we keep the ajustment
            # minimum at 0, to force the user to fill the values.
            lower = min(lower, 0)
            widget.set_adjustment(gtk.Adjustment(lower=lower, upper=upper,
                                                 step_incr=step, page_incr=page))
            return widget

        for eye in ['le', 're']:
            for element in self.optical_widgets:
                name = eye + '_' + element

                lower, upper, digits, step, page = self.optical_widgets[element]
                widget = _setup_widget(name, lower, upper, digits, step, page)
                widget.connect('validate', self._on_field_validate, element)
                widget.connect('event', self._on_event)
                if element in ['near_spherical', 'distance_spherical',
                               'addition']:
                    widget.connect_after('changed',
                                         self._after_spherical_field_changed,
                                         eye, element)

        for name in self.frame_widgets:
            lower, upper, digits, step, page = self.frame_widgets[name]
            widget = _setup_widget(name, lower, upper, digits, step, page)
            widget.connect('validate', self._on_frame_field_validate, name)
            widget.connect('event', self._on_event)

        return widget_names

    def _run_medic_editor(self, medic=None, visual_mode=False):
        with api.new_store() as store:
            parent = self.get_toplevel().get_toplevel()
            medic = run_person_role_dialog(MedicEditor, parent, store, medic,
                                           visual_mode=True)
        if medic:
            self._medic_combo_prefill()
            medic = self.store.fetch(medic)
            self.medic_combo.select(medic)

    def _medic_combo_prefill(self):
        medics = self.store.find(OpticalMedic)
        self.medic_combo.prefill(api.for_person_combo(medics))

    def setup_proxies(self):
        self._setup_widgets()
        adjustment_widgets = self._setup_adjustments()
        self.add_proxy(self.model, self.optical_wo_widgets + adjustment_widgets)

        # Update this instance proxy_widgets for OpticalWorkOrderEditor.
        # It will use this to track the changes to the model
        self.proxy_widgets += adjustment_widgets

        # Finish date should only be visible if we are creating a new workorder
        # from the sale wizard
        if self._show_finish_date:
            self.add_proxy(self._workorder, self.workorder_widgets)
        else:
            self.estimated_finish_lbl.hide()
            self.estimated_finish.hide()
            self.notes_button.hide()

    def update_visual_mode(self):
        for widget in [self.prescription_date, self.patient, self.lens_type,
                       self.frame_type, self.medic_combo, self.medic_create,
                       self.distance_box, self.near_box, self.frame_box]:
            widget.set_sensitive(False)

    #
    #   Callbacks
    #

    def _on_event(self, widget, event):
        """This callback will select the text when the user clicks the entry,
        making it easier for him to change the value
        (just like if he was navigating using the tab key)
        """
        if event.type == gtk.gdk.FOCUS_CHANGE:
            # Create a flag to control the focus change between widgets
            self._focus_change = True

        elif event.type == gtk.gdk.BUTTON_RELEASE:  # pragma: nocover
            if self._focus_change:
                # Select all text on entry box
                widget.select_region(0, -1)

            # Set flag false to avoid text selection if focus hasn't changed
            self._focus_change = False

    def _on_field_validate(self, widget, value, field):
        if value == 0:
            return

        min_v, max_v, digits, step_incr, page_incr = self.optical_widgets[field]
        if not min_v <= value <= max_v:
            return ValidationError(_(u'Value is out of range'))

        if value % step_incr != 0:
            return ValidationError(_(u'Value must be multiple of %s') %
                                   step_incr)

    def _on_frame_field_validate(self, widget, value, field):
        if value == 0:
            return

        min_v, max_v, digits, step_incr, page_incr = self.frame_widgets[field]
        if not min_v <= value <= max_v:
            return ValidationError(_(u'Value is out of range'))

        if value % step_incr != 0:
            return ValidationError(_(u'Value must be multiple of %s') %
                                   step_incr)

    def on_lens_type__changed(self, widget):
        if self.visual_mode:
            return
        has_frame = self.model.lens_type == OpticalWorkOrder.LENS_TYPE_OPHTALMIC
        self.frame_box.set_sensitive(has_frame)
        # XXX: Maybe this should be a configuration the user could toggle.
        self.medic_combo.mandatory = has_frame
        for name in ['distance_pd', 'near_pd', 'distance_height']:
            getattr(self, 'le_' + name).set_sensitive(has_frame)
            getattr(self, 're_' + name).set_sensitive(has_frame)

    def after_prescription_date__changed(self, widget):
        date = widget.read()
        if not date:
            return

        age = localtoday() - date
        if age.days > LATE_PRESCRIPTION_DAYS:
            # This is not a validation error, just a warning for the user.
            icon = widget.render_icon(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
            widget.set_pixbuf(icon)
            widget.set_tooltip(_('Attention: prescription date is older than '
                                 'one year'))
        else:
            widget.set_pixbuf(None)

    def on_estimated_finish__validate(self, widget, date):
        if date.date() < self.model.work_order.open_date.date():
            # FIXME change the string of this validation error
            return ValidationError(_(u'Estimated finish date cannot be in the '
                                     'past.'))

    def on_medic_create__clicked(self, button):
        self._run_medic_editor()

    def on_medic_combo__content_changed(self, combo):
        self.medic_details.set_sensitive(bool(self.medic_combo.read()))

    def on_medic_details__clicked(self, button):
        medic = self.model.medic
        parent = self.get_toplevel().get_toplevel()
        run_dialog(MedicEditor, parent, self.store, medic, visual_mode=True)

    # Distance axis == Near axis WHEN addition != 0

    def on_le_near_axis__value_changed(self, widget):
        if self.model.le_addition:
            self.le_distance_axis.update(widget.read())

    def on_le_distance_axis__value_changed(self, widget):
        if self.model.le_addition:
            self.le_near_axis.update(widget.read())

    def on_re_near_axis__value_changed(self, widget):
        if self.model.re_addition:
            self.re_distance_axis.update(widget.read())

    def on_re_distance_axis__value_changed(self, widget):
        if self.model.re_addition:
            self.re_near_axis.update(widget.read())

    # Distance cilindrical == Near cilindrical WHEN addition != 0

    def on_le_near_cylindrical__value_changed(self, widget):
        if self.model.le_addition:
            self.le_distance_cylindrical.update(widget.read())

    def on_le_distance_cylindrical__value_changed(self, widget):
        if self.model.le_addition:
            self.le_near_cylindrical.update(widget.read())

    def on_re_near_cylindrical__value_changed(self, widget):
        if self.model.re_addition:
            self.re_distance_cylindrical.update(widget.read())

    def on_re_distance_cylindrical__value_changed(self, widget):
        if self.model.re_addition:
            self.re_near_cylindrical.update(widget.read())

    # near_spherical = distance_spherical + addition

    def _update_spherical(self, eye, field):
        """Updates the spherical fields given the history of changes.

        This uses the last two edited fields to update the value of the third
        field.

        :param eye: The eye that was just edited ('re' or 'le')
        :param field: The field of the eye that was eddited. One of 'distance',
          'addition' or 'near'
        """
        self._update_level += 1
        last = self._update_order[eye]
        if not last or field != last[-1]:
            last.append(field)

        if len(last) > 2:
            # Remove the oldest item so we keep only the last two
            last.pop(0)

        # Current values of the model
        near = getattr(self.model, eye + '_near_spherical')
        distance = getattr(self.model, eye + '_distance_spherical')
        addition = getattr(self.model, eye + '_addition')

        if 'near_spherical' in last and 'distance_spherical' in last:
            # update addition
            widget = getattr(self, eye + '_addition')
            widget.update(near - distance)
        elif 'distance_spherical' in last and 'addition' in last:
            # update near
            near = addition and (distance + addition)
            getattr(self, eye + '_near_spherical').update(near)
        elif 'near_spherical' in last and 'addition' in last:
            # update distance
            distance = addition and (near - addition)
            getattr(self, eye + '_distance_spherical').update(distance)
        elif last == ['addition']:
            # The user didnt set neither near or distance. Just the addition.
            # But we still need to update the near field.
            near = addition and (distance + addition)
            getattr(self, eye + '_near_spherical').update(near)

        if field == 'addition' and addition == 0:
            if near:
                getattr(self, eye + '_distance_cylindrical').update(0)
                getattr(self, eye + '_distance_axis').update(0)
            else:
                getattr(self, eye + '_near_cylindrical').update(0)
                getattr(self, eye + '_near_axis').update(0)
        self._update_level -= 1

    def _after_spherical_field_changed(self, widget, eye, name):
        # This is called after near spherical, distance spherical or addition is
        # changed and is used to update the value of the other field.
        if self._update_level > 0:
            return
        self._update_spherical(eye, name)

    def on_re_addition__changed(self, widget):
        if self.model.re_near_cylindrical:
            self.re_distance_cylindrical.update(self.model.re_near_cylindrical)
        elif self.model.re_distance_cylindrical:
            self.re_near_cylindrical.update(self.model.re_distance_cylindrical)

        if self.model.re_near_axis:
            self.re_distance_axis.update(self.model.re_near_axis)
        elif self.model.re_distance_axis:
            self.re_near_axis.update(self.model.re_distance_axis)

    def on_le_addition__changed(self, widget):
        if self.model.le_near_cylindrical:
            self.le_distance_cylindrical.update(self.model.le_near_cylindrical)
        elif self.model.le_distance_cylindrical:
            self.le_near_cylindrical.update(self.model.le_distance_cylindrical)

        if self.model.le_near_axis:
            self.le_distance_axis.update(self.model.le_near_axis)
        elif self.model.le_distance_axis:
            self.le_near_axis.update(self.model.le_distance_axis)

    def on_notes_button__clicked(self, *args):
        self.store.savepoint('before_run_notes_editor')

        parent = self.get_toplevel().get_toplevel().get_toplevel()
        rv = run_dialog(NoteEditor, parent, self.store, self._workorder, 'defect_reported',
                        title=_('Observations'))
        if not rv:
            self.store.rollback_to_savepoint('before_run_notes_editor')
