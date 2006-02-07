# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005,2006 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Henrique Romano             <henrique@async.com.br>
##
""" Base class implementation for all Stoq reports """

import gettext

from kiwi.environ import environ
from stoqlib.reporting.printing import ReportTemplate
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from stoq.lib.parameters import sysparam
from stoq.lib.runtime import new_transaction
from stoq.lib.validators import format_phone_number
from stoq.domain.interfaces import ICompany

# FIXME: We must consider using TTF fonts here (UTF-8 issues)
FANCYNAME_FONT = ("Helvetica-Bold", 14)
SMALL_FONT = ("Helvetica", 12)
TEXT_HEIGHT = 13

_ = gettext.gettext

class BaseStoqReport(ReportTemplate):
    logo_border = 5 * mm

    def __init__(self, *args, **kwargs):
        ReportTemplate.__init__(self, *args, **kwargs)
        self.conn = new_transaction()
        if self.report_name:
            self.report_name = "Stoq - %s" % self.report_name
        self._logotype = self._get_logotype()
        # The BaseReportTemplate's header_height attribute define the
        # vertical position where the document really must starts be
        # drawed (this is used to not override the space reserved to
        # the logotype)
        self.header_height = (self._logotype.getSize()[1]
                              + BaseStoqReport.logo_border)
        title = self.get_title()
        if title:
            self.add_title(title)

    def _get_logotype(self):
        logofile = environ.find_resource("pixmaps", "stoq_logo_bgwhite.png")
        return ImageReader(logofile)

    def draw_header(self, canvas):
        canvas.saveState()
        person = sysparam(self.conn).CURRENT_BRANCH.get_adapted()
        company = ICompany(person)

        logo_width, logo_height = self._logotype.getSize()
        header_y = self._topMargin - logo_height - BaseStoqReport.logo_border
        header_x = self.leftMargin + BaseStoqReport.logo_border
        canvas.drawImage(self._logotype, header_x, header_y, logo_width,
                         logo_height)

        canvas.setFont(*FANCYNAME_FONT)
        text_x = header_x + logo_width + BaseStoqReport.logo_border
        text_y = header_y + logo_height - BaseStoqReport.logo_border
        canvas.drawString(text_x, text_y, company.fancy_name)

        canvas.setFont(*SMALL_FONT)
        main_address = person.get_main_address()
        address_string1 = main_address.get_address_string()
        address_string2 = ""
        if main_address.postal_code:
            address_string2 += "%s - " % main_address.postal_code
        address_string2 += "%s - %s" % (main_address.get_city(),
                                        main_address.get_state())
        contact_string = (_("Phone: %s")
                          % format_phone_number(person.phone_number))
        if person.fax_number:
            fax_str = _("Fax: %s") % format_phone_number(person.fax_number)
            contact_string += " - %s" % fax_str

        for text in (address_string1, address_string2, contact_string):
            text_y -= TEXT_HEIGHT
            canvas.drawString(text_x, text_y, text)
        canvas.restoreState()

    #
    # Hooks
    #

    def _initialize(self):
        pass

    def get_title(self):
        return ""
