# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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

""" Implementation of a generic slave for including images."""

import os
import gio
import gtk
import tempfile

from kiwi.datatypes import converter
from kiwi.ui.dialogs import save, selectfile
from kiwi.utils import gsignal

from stoqlib.domain.image import Image
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.utils.filters import get_filters_for_images
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)


class _DummyImageModel(object):
    """Dummy image model"""


class ImageSlave(BaseEditorSlave):
    """A slave for showing and editing images.

    Useful for manipulating :class:`stoqlib.domain.image.Image` obj.
    This can: Create, change, show and remove the image.
    """

    gladefile = 'ImageHolder'
    model_type = _DummyImageModel

    gsignal('image-changed', object)

    def __init__(self, store, model, can_change=True, can_erase=True,
                 visual_mode=False):
        self._image_model = model
        model = _DummyImageModel()

        BaseEditorSlave.__init__(self, store, model, visual_mode)
        self._setup_image_model()
        self._setup_widgets()

        if not can_change:
            self.edit_item.hide()
        if not can_erase:
            self.erase_item.hide()
        self._app_info = gio.app_info_get_default_for_type('image/png', False)
        if not self._app_info:
            # Hide view item if we don't have any app to visualize it.
            self.view_item.hide()

    #
    #  Private
    #

    def _setup_image_model(self):
        model = self._image_model
        if not model:
            self._image = None
            self._thumbnail = None
            return

        self._image = _pixbuf_converter.from_string(model.image)
        if model.thumbnail:
            self._thumbnail = _pixbuf_converter.from_string(model.thumbnail)
        else:
            # If image came without a thumbnail, generate one for it
            w, h = (Image.THUMBNAIL_SIZE_WIDTH, Image.THUMBNAIL_SIZE_HEIGHT)
            self._thumbnail = self._image.scale_simple(w, h,
                                                       gtk.gdk.INTERP_BILINEAR)
            self._image_model.thumbnail = (
                _pixbuf_converter.as_string(self._thumbnail))

    def _setup_widgets(self):
        self.edit_item = gtk.MenuItem(_("Change"))
        self.view_item = gtk.MenuItem(_("View"))
        self.erase_item = gtk.MenuItem(_("Erase"))
        self.save_item = gtk.MenuItem(_("Save"))
        self.popmenu = gtk.Menu()
        self.popmenu.append(self.edit_item)
        self.popmenu.append(self.view_item)
        self.popmenu.append(self.erase_item)
        self.popmenu.append(self.save_item)
        self.edit_item.connect("activate", self._on_popup_edit__activate)
        self.view_item.connect("activate", self._on_popup_view__activate)
        self.erase_item.connect("activate", self._on_popup_erase__activate)
        self.save_item.connect("activate", self._on_popup_save__activate)
        self.popmenu.show_all()
        self._update_widgets()
        if self.visual_mode:
            self.image.set_sensitive(False)

    def _update_widgets(self):
        if self._thumbnail:
            sensitive = True
            self.image.set_from_pixbuf(self._thumbnail)
        else:
            sensitive = False
            self.image.set_from_stock(gtk.STOCK_MISSING_IMAGE,
                                      gtk.ICON_SIZE_DIALOG)

        self.erase_item.set_sensitive(sensitive)
        self.view_item.set_sensitive(sensitive)
        self.save_item.set_sensitive(sensitive)

    def _save_image(self, filename=None):
        if not filename:
            name = '%s-%s.png' % ('stoq-image', self._image_model.id)
            with tempfile.NamedTemporaryFile(suffix=name, delete=False) as f:
                filename = f.name

        self._image.save(filename, "png")
        return filename

    def _view_image(self):
        filename = self._save_image()

        gfile = gio.File(path=filename)
        self._app_info.launch([gfile])

    def _edit_image(self):
        filters = get_filters_for_images()
        with selectfile(_("Select Image"), filters=filters) as sf:
            rv = sf.run()
            filename = sf.get_filename()
            if rv != gtk.RESPONSE_OK or not filename:
                return

        w, h = (Image.THUMBNAIL_SIZE_WIDTH, Image.THUMBNAIL_SIZE_HEIGHT)
        self._thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(filename, w, h)
        self._image = gtk.gdk.pixbuf_new_from_file(filename)

        if not self._image_model:
            self._image_model = Image(store=self.store)
        self._image_model.thumbnail = (
            _pixbuf_converter.as_string(self._thumbnail))
        self._image_model.image = _pixbuf_converter.as_string(self._image)
        self.emit('image-changed', self._image_model)

        self._update_widgets()

    def _erase_image(self):
        # emit needs to go first to allow removing the reference, or else
        # we won't be able to remove the Image entry from the database.
        self.emit('image-changed', None)
        Image.delete(self._image_model.id, self.store)
        self._image_model = None
        self._image = None
        self._thumbnail = None

        self._update_widgets()

    #
    #  Callbacks
    #

    def _on_popup_edit__activate(self, menu):
        self._edit_image()

    def _on_popup_view__activate(self, menu):
        self._view_image()

    def _on_popup_erase__activate(self, menu):
        self._erase_image()

    def _on_popup_save__activate(self, menu):
        model = self._image_model
        name = '%s.png' % model.get_description()
        filename = save(current_name=name,
                        folder=os.path.expanduser('~/'))
        if filename:
            self._save_image(filename)

    # image has no windows, using eventbox to catch events

    def on_eventbox__button_press_event(self, eventbox, event):
        if self.visual_mode:
            return
        if event.button == 1:
            self._edit_image()
        elif event.button == 3:
            self.popmenu.popup(None, None, None, event.button, event.time)

    def on_eventbox__enter_notify_event(self, eventbox, event):
        self.image.drag_highlight()

    def on_eventbox__leave_notify_event(self, eventbox, event):
        self.image.drag_unhighlight()
