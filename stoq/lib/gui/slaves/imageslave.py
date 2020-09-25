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

import collections
import math
import os
import tempfile

from gi.repository import Gtk, GdkPixbuf, Gio
from kiwi.datatypes import converter
from kiwi.ui.dialogs import save, selectfile
from kiwi.utils import gsignal
from storm.expr import Desc

from stoqlib.domain.image import Image
from stoqlib.domain.sellable import Sellable
from stoq.lib.gui.editors.baseeditor import BaseEditorSlave
from stoq.lib.gui.stockicons import STOQ_CHECK, STOQ_LOCKED
from stoq.lib.gui.utils.filters import get_filters_for_images
from stoqlib.lib.imageutils import get_thumbnail, get_pixbuf
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_pixbuf_converter = converter.get_converter(GdkPixbuf.Pixbuf)


class ImageSlave(BaseEditorSlave):
    """A slave for showing and editing images.

    Useful for manipulating :class:`stoqlib.domain.image.Image` obj.
    This can: Create, change, show and remove the image.
    """

    gladefile = 'ImageHolder'
    model_type = object

    gsignal('image-changed', object)

    def __init__(self, store, model, sellable=None, visual_mode=False):
        self.image_model = model
        self._updating_widgets = False
        self._sellable = sellable

        BaseEditorSlave.__init__(self, store, model, visual_mode)
        self._setup_thumbnail()
        self._setup_widgets()

        self._app_info = Gio.app_info_get_default_for_type('image/png', False)
        if not self._app_info:
            # Hide view item if we don't have any app to visualize it.
            self.view_item.hide()

    #
    #  Public API
    #

    def update_view(self):
        self._update_widgets()

    #
    #  BaseEditorSlave
    #

    def create_model(self, store):
        return object()

    #
    #  Private
    #

    def _setup_thumbnail(self):
        if not self.image_model:
            self._thumbnail = None
            return

        size = (Image.THUMBNAIL_SIZE_WIDTH, Image.THUMBNAIL_SIZE_HEIGHT)
        if not self.image_model.thumbnail:
            # If image came without a thumbnail, generate one for it
            # This should happen only once for each image
            self.image_model.thumbnail = get_thumbnail(
                self.image_model.image, size)

        self._thumbnail = get_pixbuf(self.image_model.thumbnail, fill_image=size)

    def _setup_widgets(self):
        self.set_main_item = Gtk.ImageMenuItem.new()
        self.set_main_item.set_image(Gtk.Image.new_from_icon_name(STOQ_CHECK, Gtk.IconSize.MENU))
        self.set_main_item.set_label(_("Set as main image"))
        self.set_internal_item = Gtk.CheckMenuItem(label=_("Internal use only"))
        self.view_item = Gtk.MenuItem(label=_("View"))
        self.save_item = Gtk.MenuItem(label=_("Save"))
        self.erase_item = Gtk.MenuItem(label=_("Remove"))

        self.popmenu = Gtk.Menu()
        for item, callback in [
                (self.set_main_item, self._on_popup_set_main__activate),
                (self.set_internal_item, self._on_popup_set_internal__activate),
                (self.view_item, self._on_popup_view__activate),
                (self.erase_item, self._on_popup_erase__activate),
                (self.save_item, self._on_popup_save__activate)]:
            self.popmenu.append(item)
            item.connect('activate', callback)

        self.popmenu.show_all()
        self._update_widgets()

        if self.visual_mode:
            self.image.set_sensitive(False)

    def _update_widgets(self):
        self._updating_widgets = True

        if self.image_model:
            sensitive = True
            is_main = self.image_model.is_main
            internal_use = self.image_model.internal_use
            self.image.set_from_pixbuf(self._thumbnail)
        else:
            sensitive = False
            is_main = False
            internal_use = False
            self.image.set_from_stock(Gtk.STOCK_ADD,
                                      Gtk.IconSize.DIALOG)
            self.image.set_tooltip_text(_("Add a new image"))

        self.view_item.set_sensitive(sensitive)
        self.save_item.set_sensitive(sensitive)
        self.set_main_item.set_sensitive(sensitive and not is_main)
        self.set_internal_item.set_sensitive(sensitive and not is_main)
        self.set_internal_item.set_active(internal_use)

        # Those actions only make sense for sellables
        self.set_main_item.set_visible(bool(self._sellable))
        self.set_internal_item.set_visible(bool(self._sellable))

        self.icon.set_visible(is_main or internal_use)
        if is_main:
            self.icon.set_from_icon_name(STOQ_CHECK, Gtk.IconSize.MENU)
            self.icon.set_tooltip_text(_("This is the main image"))
        elif internal_use:
            self.icon.set_from_icon_name(STOQ_LOCKED, Gtk.IconSize.MENU)
            self.icon.set_tooltip_text(_("This is for internal use only"))

        self._updating_widgets = False

    def _save_image(self, filename=None):
        if not filename:
            name = '%s-%s.png' % ('stoq-image', self.image_model.id)
            with tempfile.NamedTemporaryFile(suffix=name, delete=False) as f:
                filename = f.name

        pb = _pixbuf_converter.from_string(self.image_model.image)
        pb.savev(filename, "png", [], [])

        return filename

    def _view_image(self):
        filename = self._save_image()

        gfile = Gio.File.new_for_path(filename)
        self._app_info.launch([gfile])

    def _edit_image(self):
        filters = get_filters_for_images()
        with selectfile(_("Select Image"), filters=filters) as sf:
            rv = sf.run()
            filename = sf.get_filename()
            if rv != Gtk.ResponseType.OK or not filename:
                return

        if not self.image_model:
            self.image_model = Image(store=self.store,
                                     sellable=self._sellable)

        pb = GdkPixbuf.Pixbuf.new_from_file(filename)
        self.image_model.image = _pixbuf_converter.as_string(pb)
        self.image_model.filename = str(os.path.basename(filename))

        if self._sellable:
            for image in self._sellable.images:
                if image.is_main:
                    break
            else:
                # If there's no main image, set this one to be
                self.image_model.is_main = True

        self._setup_thumbnail()
        self.emit('image-changed', self.image_model)

        self._update_widgets()

    def _erase_image(self):
        self.store.remove(self.image_model)
        self.emit('image-changed', None)
        self.image_model = None
        self._thumbnail = None

        self._update_widgets()

    #
    #  Callbacks
    #

    def _on_popup_set_main__activate(self, menu):
        for image in self._sellable.images:
            image.is_main = False
        self.image_model.is_main = True
        # The main image cannot be set for internal use
        self.image_model.internal_use = False
        self._update_widgets()

        # FIXME: Maybe this shouldn't be necessary, but changing the main image
        # requires updating another ImageSlave's menu and icon and also
        # reordering them in the ImageGallerySlave
        self.emit('image-changed', self.image_model)

    def _on_popup_set_internal__activate(self, menu):
        if self._updating_widgets:
            return

        self.image_model.internal_use = menu.get_active()
        self._update_widgets()

    def _on_popup_view__activate(self, menu):
        self._view_image()

    def _on_popup_erase__activate(self, menu):
        self._erase_image()

    def _on_popup_save__activate(self, menu):
        fname = self.image_model.filename
        if '.' in fname:
            fname = ''.join(fname.split('.')[:-1])
        filename = save(current_name=fname + '.png',
                        folder=os.path.expanduser('~/'))
        if filename:
            self._save_image(filename)

    # image has no windows, using eventbox to catch events

    def on_eventbox__button_press_event(self, eventbox, event):
        if self.visual_mode:
            return

        if event.button in [1, 3]:
            if self.image_model is not None:
                self.popmenu.popup(None, None, None, None, event.button, event.time)
            else:
                self._edit_image()

    def on_eventbox__enter_notify_event(self, eventbox, event):
        widget = self.fixed if self.icon.get_visible() else self.image
        widget.drag_highlight()

    def on_eventbox__leave_notify_event(self, eventbox, event):
        widget = self.fixed if self.icon.get_visible() else self.image
        widget.drag_unhighlight()


class ImageGallerySlave(BaseEditorSlave):
    """Image gallery slave."""

    gladefile = 'ImageGallerySlave'
    model_type = Sellable

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self._images_per_row = None
        self._slaves = collections.OrderedDict()
        self._refresh_slaves()

    #
    #  Private
    #

    def _refresh_slaves(self):
        empty_slave = self._slaves.pop(None, None)
        # If an image was set in the empty slave, promote it
        if empty_slave is not None and empty_slave.image_model is not None:
            self._slaves[empty_slave.image_model] = empty_slave
            empty_slave = None

        # If there is no empty slave, or the old one was promoted,
        # create a new one
        if empty_slave is None:
            empty_slave = ImageSlave(self.store, None, self.model,
                                     visual_mode=self.visual_mode)
            empty_slave.connect('image-changed', self._on_image_slave__image_changed)

        # We need to reorganize the slaves because the order might have changed
        slaves = self._slaves.copy()
        self._slaves.clear()

        images = self.model.images.order_by(Desc(Image.is_main),
                                            Image.create_date)
        for image in images:
            slave = slaves.pop(image, None)
            if slave is None:
                slave = ImageSlave(self.store, image, self.model,
                                   visual_mode=self.visual_mode)
                slave.connect('image-changed', self._on_image_slave__image_changed)

            slave.update_view()
            self._slaves[image] = slave

        # The empty slave is the last one
        self._slaves[None] = empty_slave

        # Remove slaves of removed images
        for removed in slaves.values():
            removed.disconnect_by_func(self._on_image_slave__image_changed)

        self._organize(force=True)

    def _organize(self, force=False):
        if not self.images_table.get_realized():
            return

        allocation = self.sw.get_allocation()
        images_per_row = allocation.width / 180

        # Don't need to refresh if the size didn't change and we are not forcing
        if images_per_row == self._images_per_row and not force:
            return

        for child in list(self.images_table.get_children()):
            self.images_table.remove(child)

        for i, slave in enumerate(self._slaves.values()):
            row = int(math.floor(float(i) / images_per_row))
            col = i % images_per_row

            widget = slave.get_toplevel()
            widget.show()

            self.images_table.attach(widget, col, col + 1, row, row + 1,
                                     xoptions=Gtk.AttachOptions.FILL,
                                     yoptions=Gtk.AttachOptions.FILL)

        self._images_per_row = images_per_row

    #
    #  Callbacks
    #

    def _on_image_slave__image_changed(self, image_slave, image_model):
        self._refresh_slaves()

    def on_images_table__realize(self, table):
        self._organize()

    def on_sw__size_allocate(self, table, allocation):
        self._organize()
