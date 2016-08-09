# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


import collections
import glib
import gobject
import gtk

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoqlib.gui.stockicons import (STOQ_FEEDBACK,
                                    STOQ_STATUS_OK,
                                    STOQ_STATUS_WARNING,
                                    STOQ_STATUS_ERROR)
from stoqlib.lib.translation import stoqlib_gettext as _
from stoq.lib.status import ResourceStatus, ResourceStatusManager


# FIXME: Improve those strings
_status_mapper = {
    None: (
        gtk.STOCK_REFRESH,
        _("Checking status...")),
    ResourceStatus.STATUS_OK: (
        STOQ_STATUS_OK,
        _("Everything is running fine")),
    ResourceStatus.STATUS_WARNING: (
        STOQ_STATUS_WARNING,
        _("Some services are in a warning state")),
    ResourceStatus.STATUS_ERROR: (
        STOQ_STATUS_ERROR,
        _("Some services are in an error state")),
}


class StatusDialog(BasicDialog):
    size = (700, 400)
    title = _("System Status")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('size', self.size)
        kwargs.setdefault('title', self.title)

        super(StatusDialog, self).__init__(*args, **kwargs)

        self._manager = ResourceStatusManager.get_instance()
        self._manager.connect('status-changed',
                              self._on_manager__status_changed)

        self._widgets = {}
        self._setup_ui()

    #
    #  Private
    #

    def _setup_ui(self):
        self.cancel_button.hide()
        for child in self.vbox.get_children():
            self.vbox.remove(child)

        self._refresh_btn = gtk.Button(stock=gtk.STOCK_REFRESH)
        action_area = self.toplevel.get_action_area()
        action_area.pack_start(self._refresh_btn, True, True, 6)
        action_area.set_child_secondary(self._refresh_btn, True)
        self._refresh_btn.connect('clicked', self._on_refresh_btn__clicked)
        self._refresh_btn.show()

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC,
                      gtk.POLICY_AUTOMATIC)
        self.vbox.add(sw)

        viewport = gtk.Viewport()
        viewport.set_shadow_type(gtk.SHADOW_NONE)
        sw.add(viewport)

        alignment = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        alignment.set_padding(6, 6, 6, 6)
        viewport.add(alignment)

        vbox = gtk.VBox(spacing=12)
        alignment.add(vbox)

        resources = self._manager.resources.items()
        for i, (name, resource) in enumerate(resources):
            hbox = gtk.HBox(spacing=6)

            img = gtk.Image()
            hbox.pack_start(img, False, True)
            lbl = gtk.Label()
            hbox.pack_start(lbl, False, True)

            self._widgets[name] = (img, lbl)
            vbox.pack_start(hbox, False, True, 6)

            if i < len(resources) - 1:
                vbox.pack_start(gtk.HSeparator(), False, True, 0)

        self.vbox.show_all()
        self._update_ui()

    def _update_ui(self):
        for name, resource in self._manager.resources.iteritems():
            img, lbl = self._widgets[name]

            status_stock, _ignored = _status_mapper[resource.status]
            img.set_from_stock(status_stock, gtk.ICON_SIZE_LARGE_TOOLBAR)
            if resource.reason and resource.reason_long:
                text = "<b>%s</b>: %s\n<i>%s</i>" % (
                    api.escape(resource.label),
                    api.escape(resource.reason),
                    api.escape(resource.reason_long))
            elif resource.reason:
                text = "<b>%s</b>: %s" % (
                    api.escape(resource.label),
                    api.escape(resource.reason))
            else:
                text = _("Status not available...")

            lbl.set_markup(text)

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self._update_ui()

    def _on_refresh_btn__clicked(self, btn):
        self._manager.refresh_and_notify()


class StatusButton(gtk.Button):

    _BLINK_RATE = 500
    _MAX_LENGTH = 28

    def __init__(self):
        super(StatusButton, self).__init__()

        self._blink_id = None
        self._imgs = collections.deque()
        self._image = gtk.Image()
        self.set_image(self._image)

        self._manager = ResourceStatusManager.get_instance()
        self._manager.connect('status-changed',
                              self._on_manager__status_changed)

        self.set_relief(gtk.RELIEF_NONE)
        self._update_status(None)
        self._manager.refresh_and_notify(force=True)

    #
    #  Private
    #

    def _blink_icon(self):
        pixbuf = self._imgs.popleft()
        self._image.set_from_pixbuf(pixbuf)
        self._imgs.append(pixbuf)
        return True

    def _update_status(self, status):
        if self._blink_id is not None:
            glib.source_remove(self._blink_id)
            self._blink_id = None

        status_stock, text = _status_mapper[status]

        if status is not None:
            resources_str = '\n'.join(
                "[%s] %s: %s" % (r.status_str, r.label, r.reason or _("N/A"))
                for r in self._manager.resources.itervalues())
            tooltip = '%s:\n\n%s' % (text, resources_str)
        else:
            tooltip = text

        self.set_tooltip_text(tooltip)
        if len(text) > self._MAX_LENGTH:
            text = text[:self._MAX_LENGTH - 1] + u"\u2026"
        self.set_label(text)

        pixbuf = self.render_icon(status_stock, gtk.ICON_SIZE_MENU)
        self._image.set_from_pixbuf(pixbuf)

        if status not in [None, ResourceStatus.STATUS_OK]:
            self._imgs.clear()
            self._imgs.append(pixbuf)
            width = pixbuf.get_width()
            height = pixbuf.get_height()

            # Create a transparent pixbuf of the same size to create
            # the ilusion that the icon is "blinking"
            # TODO: Make the blink transition by adding more pixbufs
            # that transitions in tranparency
            empty = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,
                                   True, 8, width, height)
            empty.fill(0x00000000)
            self._imgs.append(empty)

            self._blink_id = glib.timeout_add(self._BLINK_RATE,
                                              self._blink_icon)

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self._update_status(status)


class ShellStatusbar(gtk.Statusbar):
    __gtype_name__ = 'ShellStatusbar'

    def __init__(self, window):
        gtk.Statusbar.__init__(self)
        self._disable_border()
        self.message_area = self._create_message_area()
        self._create_default_widgets()
        self.shell_window = window

    def _disable_border(self):
        # Disable border on statusbar
        children = self.get_children()
        if children and isinstance(children[0], gtk.Frame):
            frame = children[0]
            frame.set_shadow_type(gtk.SHADOW_NONE)

    def _create_message_area(self):
        for child in self.get_children():
            child.hide()
        area = gtk.HBox(False, 4)
        self.add(area)
        area.show()
        return area

    def _create_default_widgets(self):
        alignment = gtk.Alignment(0.0, 0.0, 1.0, 1.0)
        # FIXME: These looks good on Mac, might need to tweak
        # on Linux to look good
        alignment.set_padding(2, 3, 5, 5)
        self.message_area.pack_start(alignment, True, True)
        alignment.show()

        widget_area = gtk.HBox(False, 0)
        alignment.add(widget_area)
        widget_area.show()

        self._text_label = gtk.Label()
        self._text_label.set_alignment(0.0, 0.5)
        widget_area.pack_start(self._text_label, True, True)
        self._text_label.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

        self._status_button = StatusButton()
        self._status_button.connect('clicked',
                                    self._on_status_button__clicked)
        widget_area.pack_start(self._status_button, False, False, 0)
        self._status_button.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

        self._feedback_button = gtk.Button(_('Feedback'))
        image = gtk.Image()
        image.set_from_stock(STOQ_FEEDBACK, gtk.ICON_SIZE_MENU)
        self._feedback_button.set_image(image)
        image.show()
        self._feedback_button.set_can_focus(False)
        self._feedback_button.connect('clicked',
                                      self._on_feedback__clicked)
        self._feedback_button.set_relief(gtk.RELIEF_NONE)
        widget_area.pack_start(self._feedback_button, False, False, 0)
        self._feedback_button.show()

        vsep = gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

    def do_text_popped(self, ctx, text):
        self._text_label.set_label(text)

    def do_text_pushed(self, ctx, text):
        self._text_label.set_label(text)

    #
    # Callbacks
    #

    def _on_feedback__clicked(self, button):
        if self.shell_window.current_app:
            screen = self.shell_window.current_app.app_name + ' application'
        else:
            screen = 'launcher'
        run_dialog(FeedbackDialog, self.get_toplevel(), screen)

    def _on_status_button__clicked(self, button):
        run_dialog(StatusDialog, self.get_toplevel())


gobject.type_register(ShellStatusbar)
