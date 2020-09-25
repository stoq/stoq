# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#

from gi.repository import Gtk, GObject, Gio

from kiwi.utils import gsignal

from stoq.lib.gui.base.dialogs import run_dialog


def action(name, require_model=True):
    """Action decorator

    Add this to a method of a `BaseActions` subclass to mark that method as an action.

    :param name: The name of the method.
    """
    def wraper(function):
        # FIXME: shortcuts
        function.__action_spec__ = (name, require_model)
        return function

    return wraper


class BaseActions(GObject.GObject):
    #: Emitted when an object gets created.
    gsignal('model-created', object)

    #: Emitted when one or more objects get changed. Note that the object edited might be unkown
    gsignal('model-edited', object)

    #: Emitted when the model of this action group gets set. Might be useful for plugins that extend
    #: behavior of some domain.
    gsignal('model-set', object)

    #: The name of this action group. Will be used as a prefix for action names
    group_name = None

    @classmethod
    def get_instance(cls):
        if hasattr(cls, '_instance'):
            return cls._instance

        cls._instance = cls()
        return cls._instance

    def __init__(self):
        assert self.group_name
        assert not hasattr(self, '_instance')

        self.model = None
        self._actions = {}
        super(BaseActions, self).__init__()

        self.group = Gio.SimpleActionGroup()
        # register actions that were decorated with @action('ActionName')
        for key in dir(self):
            callback = getattr(self, key)
            if hasattr(callback, '__action_spec__'):
                name, require_model = callback.__action_spec__
                self.add_action(name, callback, require_model)

        self._register_action_group()

    def _register_action_group(self):
        """Register ourself in the gtk application infrastructure.
        """
        # Register the group in Gtk.Application to make it available to all
        app = Gtk.Application.get_default()
        if not app:
            app = Gtk.Application()
            Gtk.Application.set_default(app)

        window = app.get_active_window()
        if window:
            window.insert_action_group(self.group_name, self.group)
        else:
            # There is no window yet, so we must wait for one to be added to the applicattion
            def _window_added(app, window):
                window.insert_action_group(self.group_name, self.group)
                app.disconnect(self._conn_id)
            self._conn_id = app.connect('window-added', _window_added)

    def _wrapper_callback(self, action, parameter, original_callback, require_model):
        args = []
        if require_model:
            args.append(self.model)
        original_callback(*args)

    def add_action(self, name, callback, require_model):
        action = Gio.SimpleAction.new(name, None)
        # Don't connect the original callback directly so we can better handle the parameter
        # argument Gio.Action uses.
        action.connect('activate', self._wrapper_callback, callback, require_model)
        self.group.add_action(action)
        self._actions[name] = action

    def get_action(self, name):
        """Returns the Gio.Action given its name"""
        return self._actions[name]

    def run_dialog(self, dialog, *args, **kwargs):
        return run_dialog(dialog, None, *args, **kwargs)

    def set_action_enabled(self, action, sensitive):
        """Enables or disables an action

        :param action: the action name
        :param sensitive: If the action is enabled or disabled
        """
        action = self._actions[action]
        action.set_enabled(bool(sensitive))

    def set_model(self, model):
        """Sets the model this action group is currently handling.

        For actions that change the state of an object, this is the object that will be updated.
        """
        self.model = model
        self.model_set(model)
        self.emit('model-set', model)
