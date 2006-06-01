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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Slaves for till management """

from kiwi.ui.delegates import SlaveDelegate



class TillFiscalOperationsToolbar(SlaveDelegate):
    """ A simple sale toolbar with common operations like, returning a sale,
    changing installments and showing its details.
    """
    gladefile = "TillFiscalOperationsToolbar"

    def __init__(self):
        gladefile = TillFiscalOperationsToolbar.gladefile
        SlaveDelegate.__init__(self, gladefile=gladefile,
                               toplevel_name=gladefile)

    def set_tillout_button_sensitive(self, value):
        self.till_out_button.set_sensitive(value)

    def set_resume_button_sensitive(self, value):
        self.resume_button.set_sensitive(value)

    #
    # Kiwi callbacks
    #

    def on_resume_button__clicked(self, *args):
        pass

    def on_till_out_button__clicked(self, *args):
        pass
