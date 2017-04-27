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
from gi.repository import Gtk, GObject, GLib, GdkPixbuf

from stoqlib.api import api
from stoqlib.gui.base.dialogs import BasicDialog, run_dialog
from stoqlib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.stockicons import (STOQ_FEEDBACK,
                                    STOQ_STATUS_NA,
                                    STOQ_STATUS_OK,
                                    STOQ_STATUS_WARNING,
                                    STOQ_STATUS_ERROR)
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.threadutils import terminate_thread
from stoq.lib.status import ResourceStatus, ResourceStatusManager


# FIXME: Improve those strings
_status_mapper = {
    None: (
        Gtk.STOCK_REFRESH,
        _("Checking status...")),
    ResourceStatus.STATUS_NA: (
        STOQ_STATUS_NA,
        _("Status not available")),
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
        self._manager.connect('action-finished',
                              self._on_manager__action_finished)

        with api.new_store() as store:
            user = api.get_current_user(store)
            self._is_admin = user.profile.check_app_permission(u'admin')

        self._widgets = {}
        self._setup_ui()

    #
    #  Private
    #

    def _setup_ui(self):
        self.cancel_button.hide()
        for child in self.vbox.get_children():
            self.vbox.remove(child)

        self._refresh_btn = Gtk.Button(stock=Gtk.STOCK_REFRESH)
        action_area = self.toplevel.get_action_area()
        action_area.pack_start(self._refresh_btn, True, True, 6)
        action_area.set_child_secondary(self._refresh_btn, True)
        self._refresh_btn.connect('clicked', self._on_refresh_btn__clicked)
        self._refresh_btn.show()

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC,
                      Gtk.PolicyType.AUTOMATIC)
        self.vbox.add(sw)

        viewport = Gtk.Viewport()
        viewport.set_shadow_type(Gtk.ShadowType.NONE)
        sw.add(viewport)

        alignment = Gtk.Alignment.new(0.0, 0.0, 1.0, 1.0)
        alignment.set_padding(6, 6, 6, 6)
        viewport.add(alignment)

        vbox = Gtk.VBox(spacing=12)
        alignment.add(vbox)

        resources = self._manager.resources.items()
        for i, (name, resource) in enumerate(resources):
            hbox = Gtk.HBox(spacing=6)

            img = Gtk.Image()
            hbox.pack_start(img, False, True, 0)
            lbl = Gtk.Label()
            hbox.pack_start(lbl, False, True, 0)

            buttonbox = Gtk.HButtonBox()
            hbox.pack_end(buttonbox, False, True, 0)

            self._widgets[name] = (img, lbl, buttonbox)
            vbox.pack_start(hbox, False, True, 6)

            if i < len(resources) - 1:
                separator = Gtk.HSeparator()
                vbox.pack_start(separator, False, True, 0)

        self.vbox.show_all()
        self._update_ui()

    def _update_ui(self):
        running_action = self._manager.running_action
        self._refresh_btn.set_sensitive(running_action is None)

        for name, resource in self._manager.resources.iteritems():
            img, lbl, buttonbox = self._widgets[name]

            status_stock, _ignored = _status_mapper[resource.status]
            img.set_from_stock(status_stock, Gtk.IconSize.LARGE_TOOLBAR)
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

            for child in buttonbox.get_children():
                buttonbox.remove(child)
            for action in resource.get_actions():
                btn = Gtk.Button(action.label)

                if running_action is not None:
                    btn.set_sensitive(False)

                if action.admin_only and not self._is_admin:
                    btn.set_sensitive(False)
                    btn.set_tooltip_text(
                        _("Only admins can execute this action"))

                # If the action is the running action, add a spinner together
                # with the label to indicate that it is running
                if action == running_action:
                    spinner = Gtk.Spinner()
                    hbox = Gtk.HBox(spacing=6)
                    child = btn.get_child()
                    btn.remove(child)
                    hbox.add(child)
                    hbox.add(spinner)
                    btn.add(hbox)
                    spinner.start()
                    hbox.show_all()

                btn.show()
                btn.connect('clicked', self._on_action_btn__clicked, action)
                buttonbox.add(btn)

            lbl.set_markup(text)

    def _handle_action(self, action):
        retval = self._manager.handle_action(action)
        if action.threaded:
            thread = retval

            msg = _('Executing "%s". This might take a while...') % (
                action.label, )
            progress_dialog = ProgressDialog(msg, pulse=True)
            progress_dialog.start(wait=100)
            progress_dialog.set_transient_for(self.get_toplevel())
            progress_dialog.set_title(action.resource.label)
            progress_dialog.connect(
                'cancel', lambda d: terminate_thread(thread))

            while thread.is_alive():
                if Gtk.events_pending():
                    Gtk.main_iteration_do(False)

            progress_dialog.stop()

        self._update_ui()

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self._update_ui()

    def _on_manager__action_finished(self, manager, action, retval):
        if isinstance(retval, Exception):
            warning(_('An error happened when executing "%s"') % (action.label, ),
                    str(retval))
        self._update_ui()

    def _on_action_btn__clicked(self, btn, action):
        self._handle_action(action)

    def _on_refresh_btn__clicked(self, btn):
        self._manager.refresh_and_notify()


class StatusButton(Gtk.Button):

    __gtype_name__ = 'StatusButton'
    _BLINK_RATE = 500
    _MAX_LENGTH = 28

    def __init__(self):
        super(StatusButton, self).__init__()

        self._blink_id = None
        self._imgs = collections.deque()
        self._image = Gtk.Image()
        self.set_image(self._image)

        self._manager = ResourceStatusManager.get_instance()
        self._manager.connect('status-changed',
                              self._on_manager__status_changed)

        self.set_relief(Gtk.ReliefStyle.NONE)
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
            GLib.source_remove(self._blink_id)
            self._blink_id = None

        status_stock, text = _status_mapper[status]

        if status is not None:
            tooltip = '\n'.join(
                "[%s] %s: %s" % (r.status_str, r.label, r.reason or _("N/A"))
                for r in self._manager.resources.itervalues())
        else:
            tooltip = ''

        self.set_tooltip_text(tooltip)

        pixbuf = self.render_icon(status_stock, Gtk.IconSize.MENU)
        self._image.set_from_pixbuf(pixbuf)

        if status not in [None,
                          ResourceStatus.STATUS_NA,
                          ResourceStatus.STATUS_OK]:
            self._imgs.clear()
            self._imgs.append(pixbuf)
            width = pixbuf.get_width()
            height = pixbuf.get_height()

            # Create a transparent pixbuf of the same size to create
            # the ilusion that the icon is "blinking"
            # TODO: Make the blink transition by adding more pixbufs
            # that transitions in tranparency
            empty = GdkPixbuf.Pixbuf.new(
                GdkPixbuf.Colorspace.RGB, True, 8, width, height)
            empty.fill(0x00000000)
            self._imgs.append(empty)

            self._blink_id = GLib.timeout_add(self._BLINK_RATE,
                                              self._blink_icon)

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self._update_status(status)


GObject.type_register(StatusButton)


class ShellStatusbar(Gtk.Statusbar):
    __gtype_name__ = 'ShellStatusbar'

    def __init__(self, window):
        super(ShellStatusbar, self).__init__()

        self._disable_border()
        self.message_area = self._create_message_area()
        self._create_default_widgets()
        self.shell_window = window

    def _disable_border(self):
        # Disable border on statusbar
        children = self.get_children()
        if children and isinstance(children[0], Gtk.Frame):
            frame = children[0]
            frame.set_shadow_type(Gtk.ShadowType.NONE)

    def _create_message_area(self):
        for child in self.get_children():
            child.hide()
        area = Gtk.HBox(False, 4)
        self.add(area)
        area.show()
        return area

    def _create_default_widgets(self):
        alignment = Gtk.Alignment.new(0.0, 0.0, 1.0, 1.0)
        # FIXME: These looks good on Mac, might need to tweak
        # on Linux to look good
        alignment.set_padding(2, 3, 5, 0)
        self.message_area.pack_start(alignment, True, True, 0)
        alignment.show()

        widget_area = Gtk.HBox(False, 0)
        alignment.add(widget_area)
        widget_area.show()

        self._text_label = Gtk.Label()
        self._text_label.set_hexpand(True)
        self._text_label.set_alignment(0.0, 0.5)
        widget_area.pack_start(self._text_label, True, True, 0)
        self._text_label.show()

        vsep = Gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

        self._feedback_button = Gtk.Button(_('Feedback'))
        image = Gtk.Image()
        image.set_from_stock(STOQ_FEEDBACK, Gtk.IconSize.MENU)
        self._feedback_button.set_image(image)
        image.show()
        self._feedback_button.set_can_focus(False)
        self._feedback_button.connect('clicked',
                                      self._on_feedback__clicked)
        self._feedback_button.set_relief(Gtk.ReliefStyle.NONE)
        widget_area.pack_start(self._feedback_button, False, False, 0)
        self._feedback_button.show()

        vsep = Gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

        self._status_button = StatusButton()
        self._status_button.connect('clicked',
                                    self._on_status_button__clicked)
        self.message_area.pack_end(self._status_button, False, False, 0)
        self._status_button.show()

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


GObject.type_register(ShellStatusbar)
