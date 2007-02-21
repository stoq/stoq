# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Henrique Romano             <henrique@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Base classes for editors """

from kiwi.log import Logger
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.widgets.label import ProxyLabel

from stoqlib.lib.component import Adapter
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.dialogs import BasicWrappingDialog

log = Logger('stoqlib.gui.editors')

_ = stoqlib_gettext

class BaseEditorSlave(GladeSlaveDelegate):
    """ Base class for editor slaves inheritance. It offers methods for
    setting up focus sequence, required attributes and validated attrs.

    @cvar gladefile:
    @cvar model_type:
    @cvar model_iface:
    """
    gladefile = None
    model_type = None
    model_iface = None
    proxy_widgets = ()

    def __init__(self, conn, model=None, visual_mode=False):
        """
        @param conn: a connection
        @param model: the object model tied with the proxy widgets
        @param visual_mode: does this slave must be opened in visual mode?
                            if so, all the proxy widgets will be disable
        """
        self.conn = self.trans = conn
        self.edit_mode = model is not None
        self.visual_mode = visual_mode

        if model:
            created = ""
        else:
            created = "created "
            model = self.create_model(self.conn)

        log.info("%s editor using a %smodel %s" % (
            self.__class__.__name__, created, type(model).__name__))

        if not model:
            raise ValueError("Editors must define a model at this point")

        if self.model_iface:
            if not isinstance(model, Adapter):
                model = self.model_iface(model)
            elif not self.model_iface.providedBy(model):
                raise TypeError(
                    "%s editor requires a model implementing %s, got a %r" % (
                    self.__class__.__name__, self.model_iface.__name__,
                    model))
            self.model_type = self.model_type or type(model)

        elif self.model_type:
            if not isinstance(model, self.model_type):
                raise TypeError(
                    '%s editor requires a model of type %s, got a %r' % (
                    self.__class__.__name__, self.model_type.__name__,
                    model))
        else:
            raise ValueError("Editors must define a model_type or "
                             "model_iface attributes")
        self.model = model

        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        if self.visual_mode:
            self._setup_visual_mode()
        self.setup_proxies()
        self.setup_slaves()

    def _setup_visual_mode(self):
        widgets = self.__class__.proxy_widgets
        for widget_name in widgets:
            widget = getattr(self, widget_name)
            if isinstance(widget, ProxyLabel):
                continue
            widget.set_sensitive(False)
        self.update_visual_mode()

    def create_model(self, trans):
        """
        Creates a new model for the editor.
        After this method is called, the model can be accessed as self.model.
        The default behavior is to raise a TypeError, which can
        be overridden in a subclass.
        @param trans: a database transaction
        """
        raise TypeError("%r needs a model, got None. Perhaps you want to "
                        "implement create_model?" % self)

    def setup_proxies(self):
        """
        A subclass can override this
        """

    def setup_slaves(self):
        """
        A subclass can override this
        """

    #
    # Hook methods
    #

    def on_cancel(self):
        """ This is a hook method which must be redefined when some
        action needs to be executed when cancelling in the dialog. """
        return False

    def on_confirm(self):
        """ This is a hook method which must be redefined when some
        action needs to be executed when confirming in the dialog. """
        return self.model

    def update_visual_mode(self):
        """This method must be overwritten on child if some addition task in
        visual mode are needed
        """

    def validate_confirm(self):
        """ Must be redefined by childs and will perform some validations
        after the click of ok_button. It is interesting to use with some
        special validators that provide some tasks over more than one widget
        value """
        return True


class BaseEditor(BaseEditorSlave):
    """ Base class for editor dialogs. It offers methods of
    BaseEditorSlave, a windows title and OK/Cancel buttons.

    @cvar model_name: the model type name of the model we are editing.
       This value will be showed in the title of the editor and can not
       be merely the attribute __name__ of the object for usability reasons.
       Call sites will decide what could be the best name applicable in each
       situation.
    """

    model_name = None
    header = ''
    size = ()
    title = None
    hide_footer = False

    def __init__(self, conn, model=None, visual_mode=False):
        BaseEditorSlave.__init__(self, conn, model,
                                 visual_mode=visual_mode)

        # We can not use self.model for get_title since we will create a new
        # one in BaseEditorSlave if model is None.
        self.main_dialog = BasicWrappingDialog(self,
                                               self.get_title(self.model),
                                               self.header, self.size)


        if self.hide_footer or self.visual_mode:
            self.main_dialog.hide_footer()

        self.register_validate_function(self.refresh_ok)
        self.force_validation()

    def _get_title_format(self):
        if self.visual_mode:
            return _(u"Details of %s")
        if self.edit_mode:
            return _(u'Edit Details of "%s"')
        return _(u"Add %s")

    def get_title(self, model):
        if self.title:
            return self.title
        if not model:
            raise ValueError("A model should be defined at this point")

        title_format = self._get_title_format()
        if self.model_name:
            model_name = self.model_name
        else:
            # Fallback to the name of the class
            model_name = type(self.model).__name__

        return title_format % model_name

    def set_description(self, description):
        """
        Sets the description of the model object which is used by the editor
        @param description:
        """
        format = self._get_title_format()
        self.main_dialog.set_title(format % description)

    def refresh_ok(self, validation_value):
        """ Refreshes ok button sensitivity according to widget validators
        status """
        self.main_dialog.ok_button.set_sensitive(validation_value)
