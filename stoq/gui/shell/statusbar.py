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
from gi.repository import Gtk, GObject, GLib

from stoqlib.api import api
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.dialogs.feedbackdialog import FeedbackDialog
from stoq.lib.gui.dialogs.progressdialog import ProgressDialog
from stoq.lib.gui.stockicons import (STOQ_FEEDBACK,
                                     STOQ_REFRESH,
                                     STOQ_STATUS_NA,
                                     STOQ_STATUS_OK,
                                     STOQ_STATUS_WARNING,
                                     STOQ_STATUS_ERROR)
from stoqlib.lib.translation import stoqlib_gettext as _
from stoqlib.lib.threadutils import terminate_thread
from stoq.lib.status import ResourceStatus, ResourceStatusManager


# FIXME: Improve those strings
_status_mapper = {
    None: (
        STOQ_REFRESH,
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


class ResourceStatusBox(Gtk.Box):
    def __init__(self, resource, manager, compact=False):
        self._resource = resource
        self._compact = compact
        self._manager = manager
        user = api.get_current_user(api.get_default_store())
        self._is_admin = user.profile.check_app_permission(u'admin')

        super(ResourceStatusBox, self).__init__(spacing=6)
        if compact:
            self.props.margin = 6
        else:
            self.props.margin = 12

        self.img = Gtk.Image()
        self.pack_start(self.img, False, True, 0)
        self.lbl = Gtk.Label()
        self.lbl.set_xalign(0)
        self.lbl.set_line_wrap(True)
        self.pack_start(self.lbl, False, True, 0)

        self.buttonbox = Gtk.Box()
        self.buttonbox.set_valign(Gtk.Align.CENTER)
        self.buttonbox.get_style_context().add_class('linked')
        if not compact:
            self.pack_end(self.buttonbox, False, True, 0)

    def add_action(self, action):
        running_action = self._manager.running_action
        btn = Gtk.Button.new_with_label(action.label)

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
        self.buttonbox.add(btn)
        return btn

    def update_ui(self):
        resource = self._resource
        if self._compact:
            # Only show waring and error messages in compact mode
            self.set_visible(resource.status in [ResourceStatus.STATUS_ERROR,
                                                 ResourceStatus.STATUS_WARNING])

        status_icon, _ignored = _status_mapper[resource.status]
        icon_size = Gtk.IconSize.LARGE_TOOLBAR
        if self._compact:
            icon_size = Gtk.IconSize.BUTTON
        self.img.set_from_icon_name(status_icon, icon_size)

        tooltip = ''
        if self._compact and resource.reason:
            text = api.escape(resource.reason)
            tooltip = "<b>%s</b>: %s\n<i>%s</i>" % (
                api.escape(resource.label),
                api.escape(resource.reason),
                api.escape(resource.reason_long))
        elif resource.reason and resource.reason_long:
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

        # Remove old actions and add new ones
        for child in self.buttonbox.get_children():
            self.buttonbox.remove(child)
        for action in resource.get_actions():
            self.add_action(action)

        self.lbl.set_markup(text)
        self.set_tooltip_markup(tooltip)

    def _on_action_btn__clicked(self, btn, action):
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

        self.update_ui()


class StatusBox(Gtk.Bin):
    size = (650, 400)

    def __init__(self, compact=False):
        super(StatusBox, self).__init__()
        self._compact = compact

        self._manager = ResourceStatusManager.get_instance()

        self._widgets = {}
        self._setup_ui()

        self._manager.connect('status-changed', self._on_manager__status_changed)
        self._manager.connect('action-started', self._on_manager__action_started)
        self._manager.connect('action-finished', self._on_manager__action_finished)

    #
    #  Private
    #

    def _create_widget(self, resource_name, resource):
        box = ResourceStatusBox(resource, self._manager, self._compact)

        row = Gtk.ListBoxRow()
        row.add(box)
        row.set_activatable(False)
        self.box.add(row)
        self._widgets[resource_name] = box
        row.show_all()
        box.update_ui()

    def _setup_ui(self):
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.vbox)
        self._refresh_btn = Gtk.Button.new_from_icon_name(STOQ_REFRESH, Gtk.IconSize.BUTTON)
        self._refresh_btn.set_label(_('Refresh'))
        self._refresh_btn.set_relief(Gtk.ReliefStyle.NONE)
        self._refresh_btn.connect('clicked', self._on_refresh_btn__clicked)

        action_area = Gtk.ButtonBox()
        if not self._compact:
            action_area.pack_start(self._refresh_btn, True, True, 6)
        action_area.set_layout(Gtk.ButtonBoxStyle.END)

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER,
                      Gtk.PolicyType.AUTOMATIC)
        self.vbox.pack_start(sw, expand=True, fill=True, padding=0)
        self.vbox.pack_start(action_area, expand=False, fill=True, padding=0)

        viewport = Gtk.Viewport()
        viewport.set_shadow_type(Gtk.ShadowType.NONE)
        sw.add(viewport)

        self.box = Gtk.ListBox()
        # This will remove the white background in the list
        self.box.get_style_context().add_class('transparent')
        self.box.set_selection_mode(Gtk.SelectionMode.NONE)

        def create_header(row, previous):
            if previous:
                row.set_header(Gtk.HSeparator())
        if not self._compact:
            self.box.set_header_func(create_header)

        viewport.add(self.box)
        self.vbox.show_all()
        self.update_ui()

    def update_ui(self):
        running_action = self._manager.running_action
        self._refresh_btn.set_sensitive(running_action is None)

        for name, resource in self._manager.resources.items():
            if name not in self._widgets:
                self._create_widget(name, resource)
            box = self._widgets[name]
            box.update_ui()

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self.update_ui()

    def _on_manager__action_started(self, manager, action):
        self.update_ui()

    def _on_manager__action_finished(self, manager, action, retval):
        self.update_ui()

    def _on_refresh_btn__clicked(self, btn):
        self._manager.refresh_and_notify()


class StatusPopover(Gtk.Popover):
    size = (650, 400)

    def __init__(self):
        super(StatusPopover, self).__init__()
        self.set_size_request(*self.size)
        box = StatusBox()
        self.add(box)
        box.show()


class StatusButton(Gtk.MenuButton):

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
        self.set_popover(StatusPopover())

    #
    #  Private
    #

    def _blink_icon(self):
        icon_name = self._imgs.popleft()
        if icon_name:
            self._image.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
        else:
            self._image.clear()
        self._imgs.append(icon_name)
        return True

    def _update_status(self, status):
        if self._blink_id is not None:
            GLib.source_remove(self._blink_id)
            self._blink_id = None

        status_icon, text = _status_mapper[status]

        if status is not None:
            tooltip = '\n'.join(
                "[%s] %s: %s" % (r.status_str, r.label, r.reason or _("N/A"))
                for r in self._manager.resources.values())
        else:
            tooltip = ''

        self.set_tooltip_text(tooltip)

        self._image.set_from_icon_name(status_icon, Gtk.IconSize.MENU)
        self._image.set_size_request(16, 16)

        if status not in [None,
                          ResourceStatus.STATUS_NA,
                          ResourceStatus.STATUS_OK]:
            self._imgs.clear()
            self._imgs.append(status_icon)
            # This 'empty image' will be used for blinking
            self._imgs.append(None)
            self._blink_id = GLib.timeout_add(self._BLINK_RATE,
                                              self._blink_icon)

    #
    #  Callbacks
    #

    def _on_manager__status_changed(self, manager, status):
        self._update_status(status)
        self.set_popover(StatusPopover())


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
        area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add(area)
        area.show()
        return area

    def _create_default_widgets(self):
        widget_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.message_area.pack_start(widget_area, True, True, 0)
        widget_area.show()

        self._text_label = Gtk.Label()
        self._text_label.set_hexpand(True)
        self._text_label.set_xalign(0.0)
        self._text_label.set_yalign(0.5)
        widget_area.pack_start(self._text_label, True, True, 0)
        self._text_label.show()

        vsep = Gtk.VSeparator()
        widget_area.pack_start(vsep, False, False, 0)
        vsep.show()

        self._feedback_button = Gtk.Button.new_with_label(_('Feedback'))
        image = Gtk.Image()
        image.set_from_icon_name(STOQ_FEEDBACK, Gtk.IconSize.BUTTON)
        self._feedback_button.set_image(image)
        image.show()
        self._feedback_button.set_can_focus(False)
        self._feedback_button.connect('clicked',
                                      self._on_feedback__clicked)
        self._feedback_button.set_relief(Gtk.ReliefStyle.NONE)
        widget_area.pack_start(self._feedback_button, False, False, 0)
        self._feedback_button.show()

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


GObject.type_register(ShellStatusbar)
