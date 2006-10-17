# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##  Author(s):      Bruno Rafael Garcia     <brg@async.com.br>
##                  Evandro Vale Miquelito  <evandro@async.com.br>
##                  Johan Dahlin            <jdahlin@async.com.br>
##

# TODO: Rename/Move parts to stoqlib/gui/editors/usereditor.py ?

""" User editor slaves implementation.  """

from sqlobject.sqlbuilder import func
from kiwi.datatypes import ValidationError

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import validate_password
from stoqlib.gui.base.editors import BaseEditor, BaseEditorSlave
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.profileeditor import UserProfileEditor
from stoqlib.domain.profile import UserProfile
from stoqlib.domain.person import EmployeeRole, Person
from stoqlib.domain.interfaces import IEmployee, ISalesPerson, IUser


_ = stoqlib_gettext

class LoginInfo:
    """ This class is used by password editor only for validation of the
        fields.
    """
    current_password = None
    new_password = None
    confirm_password = None

class UserStatusSlave(BaseEditorSlave):
    gladefile = 'UserStatusSlave'
    model_iface = IUser
    proxy_widgets = ('active_check',)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    UserStatusSlave.proxy_widgets)


class PasswordEditorSlave(BaseEditorSlave):
    """ A slave for asking (and confirming) password; Optionally, this slave
    can be used just to ask the password once, i.e, not displaying the entry
    for confirmation (see confirm_password parameter).
    """
    gladefile = 'PasswordEditorSlave'
    model_type = LoginInfo
    proxy_widgets = ('password',
                     'confirm_password')

    def __init__(self, conn, model=None, visual_mode=False,
                 confirm_password=True):
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)
        self._confirm_password = confirm_password
        self._setup_widgets()

    def _setup_widgets(self):
        if not self._confirm_password:
            self.confirm_password_lbl.hide()
            self.confirm_password.hide()

    def invalidate_password(self, message):
        self.password.set_invalid(message)

    #
    # Hooks
    #

    def set_password_labels(self, password_lbl, confirm_password):
        self.password_lbl.set_text(password_lbl)
        self.confirm_password_lbl.set_text(confirm_password)

    #
    # BaseEditorSlave Hooks
    #

    def create_model(self, conn):
        return LoginInfo()

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    PasswordEditorSlave.proxy_widgets)

    def validate_confirm(self):
        # If we aren't confirming passwords, we don't need to validate
        # it, i.e, when asking the password once, we just wants to
        # compare it to the stored password and check if they matches,
        # no need to check the text lenght, nor anything related to
        # security.
        if not self._confirm_password:
            return True
        callback = lambda msg: self.password.set_invalid(msg)
        new_passwd = self.model.new_password
        if not validate_password(new_passwd, callback):
            return False
        callback = lambda msg: self.confirm_password.set_invalid(msg)
        confirm_passwd = self.model.confirm_password
        if not validate_password(confirm_passwd, callback):
            return False
        if confirm_passwd != new_passwd:
            msg = _(u"New password and confirm password don't match")
            self.password.set_invalid(msg)
            return False
        return True


class PasswordEditor(BaseEditor):
    gladefile = 'PasswordEditor'
    model_type = LoginInfo
    proxy_widgets = ('current_password',)

    def __init__(self, conn, user, visual_mode=False):
        self.user = user
        self.old_password = self.user.password
        BaseEditor.__init__(self, conn, visual_mode=visual_mode)
        self._setup_widgets()

    def _setup_widgets(self):
        self.password_slave.set_password_labels(_('New Password:'),
                                                _('Retype New Password:'))

    #
    # BaseEditorSlave Hooks
    #

    def get_title(self, model):
        title = _('Change "%s" Password') % self.user.username
        return title

    def create_model(self, conn):
        return LoginInfo()

    def setup_slaves(self):
        self.password_slave = PasswordEditorSlave(self.conn, self.model,
                                                  visual_mode=self.visual_mode)
        self.attach_slave('password_holder', self.password_slave)

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    PasswordEditor.proxy_widgets)

    def validate_confirm(self):
        if self.model.current_password != self.old_password:
            msg = _(u"Password doesn't match with the stored one")
            self.current_password.set_invalid(msg)
            return False
        if not self.password_slave.validate_confirm():
            return False
        return True

    def on_confirm(self):
        self.password_slave.on_confirm()
        self.user.password = self.model.new_password
        return self.user

class UserDetailsSlave(BaseEditorSlave):
    gladefile = 'UserDetailsSlave'
    model_iface = IUser
    proxy_widgets = ('username',
                     'profile')

    def __init__(self, conn, model, show_password_fields=True,
                 visual_mode=False):
        self.show_password_fields = show_password_fields
        BaseEditorSlave.__init__(self, conn, model, visual_mode=visual_mode)

    def _setup_widgets(self):
        if self.show_password_fields:
            self._attach_slaves()
            self.change_password_button.hide()
        self._setup_entry_completion()

    def _setup_entry_completion(self):
        if self.model.profile is None:
            self.model.profile = UserProfile.get_default(conn=self.conn)
        profiles = UserProfile.select(connection=self.conn, orderBy='name')
        self.profile.prefill([(p.name, p) for p in profiles])

    def _attach_slaves(self):
        self.password_slave = PasswordEditorSlave(self.conn)
        self.attach_slave('password_holder', self.password_slave)

    #
    # BaseEditorSlave Hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    UserDetailsSlave.proxy_widgets)

    def validate_confirm(self):
        if self.show_password_fields:
            return self.password_slave.validate_confirm()
        return True

    def on_confirm(self):
        if self.show_password_fields:
            self.model.password = self.password_slave.model.new_password

        # FIXME:
        # 1) Move this hook into each instance of ProfileSettings
        # 2) Show some additional information in the user interface, which
        #    are related to the facets the current profile will add
        profile = self.profile.get_selected()
        if profile.name == 'Salesperson':
            role = EmployeeRole.selectOneBy(name=profile.name,
                                            connection=self.conn)
            person = self.model.person
            person.addFacet(IEmployee, role=role, connection=self.conn)
            person.addFacet(ISalesPerson, connection=self.conn)

    #
    # Kiwi handlers
    #

    def on_username__validate(self, widget, value):
        # FIXME: Move to Person/IUser
        user_table = Person.getAdapterClass(IUser)
        query = func.UPPER(user_table.q.username) == value.upper()
        user = Person.iselectOne(IUser, query, connection=self.conn)
        if user and self.model.username != value:
            return ValidationError('Username already exist')

    def on_profile_button__clicked(self, button):
        user_profile = self.model.profile
        if run_dialog(UserProfileEditor, self, self.conn, user_profile):
            self._setup_entry_completion()
            self.proxy.update('profile')


    def on_change_password_button__clicked(self, *args):
        model = run_dialog(PasswordEditor, self, self.conn, self.model)

