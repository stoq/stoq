# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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
##
"""Feedback dialog"""

import logging

import gtk
from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.webservice import WebService

log = logging.getLogger(__name__)
_ = stoqlib_gettext


class Feedback(object):
    def __init__(self):
        self.email = api.user_settings.get('feedback-email')
        self.feedback = ""


class FeedbackDialog(BaseEditor):
    model_name = _('Stoq feedback')
    model_type = Feedback
    gladefile = 'FeedbackDialog'
    proxy_widgets = ['email', 'feedback']
    size = (350, 240)

    def __init__(self, application_screen=None):
        # FIXME: BaseEditor expects a store, so we are passing one here, even
        # though it won't be used. We should be inheriting from BaseDialog.
        BaseEditor.__init__(self, api.get_default_store())
        self.main_dialog.set_title(self.model_name)
        self.application_screen = application_screen

    def create_model(self, unused):
        return Feedback()

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)
        self.feedback.set_wrap_mode(gtk.WRAP_WORD)
        if self.model.email:
            self.feedback.grab_focus()
        else:
            self.email.grab_focus()

    def validate_confirm(self):
        if not self._can_submit_feedback():
            return False

        webapi = WebService()
        d = webapi.feedback(self.application_screen,
                            self.model.email,
                            self.model.feedback)
        d.addCallback(self._on_feedback_reply)
        self.disable_ok()
        return False

    def _can_submit_feedback(self):
        return '@' in self.model.email and self.model.feedback

    def _on_feedback_reply(self, details):
        log.info("Feedback details: %s" % (details, ))
        api.user_settings.set('feedback-email', self.model.email)
        self.retval = self.model
        self.main_dialog.close()

    #
    # Callbacks
    #

    def on_email__validate(self, widget, email):
        if not '@' in email:
            return ValidationError(
                _("%s is not a valid email address") % (email, ))
