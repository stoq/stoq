# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Base class implementation for all Stoq reports """

import tempfile

import gtk

from kiwi.datatypes import converter, ValidationError
from kiwi.environ import environ
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

from stoqlib.database.runtime import (get_current_branch, get_default_store,
                                      get_current_user)
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.base.printing import ReportTemplate

_ = stoqlib_gettext


FANCYNAME_FONT = ("Vera-B", 14)
LOGO_SIZE = (170, 65)
SMALL_FONT = ("Vera", 12)
TEXT_HEIGHT = 13


def get_logotype_path(store):
    logo_domain = sysparam(store).CUSTOM_LOGO_FOR_REPORTS
    if logo_domain and logo_domain.image:
        pixbuf_converter = converter.get_converter(gtk.gdk.Pixbuf)
        try:
            pixbuf = pixbuf_converter.from_string(logo_domain.image)
        except ValidationError:
            pixbuf = None

        if pixbuf:
            w, h = LOGO_SIZE
            ow, oh = pixbuf.props.width, pixbuf.props.height
            if ow > oh:
                w = int(h * (ow / float(oh)))
            else:
                w = int(h * (oh / float(ow)))

            pixbuf = pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)
            tmp_file = tempfile.NamedTemporaryFile(prefix='stoq-logo')
            tmp_file.close()
            pixbuf.save(tmp_file.name, 'png')
            return tmp_file.name

    return environ.find_resource("pixmaps", "stoq_logo_bgwhite.png")


class BaseStoqReport(ReportTemplate):
    logo_border = 4 * mm
    report_name_prefix = "Stoq - "

    def __init__(self, *args, **kwargs):
        timestamp = kwargs.get('do_footer', True)
        ReportTemplate.__init__(self, timestamp=timestamp,
                                username=self.get_username(), *args, **kwargs)
        logotype_path = get_logotype_path(get_default_store())
        self._logotype = ImageReader(logotype_path)
        # The BaseReportTemplate's header_height attribute define the
        # vertical position where the document really must starts be
        # drawed (this is used to not override the space reserved to
        # the logotype)
        self.header_height = LOGO_SIZE[1]
        title = self.get_title()
        if title:
            if not type(title) is tuple:
                title = (title, )
            self.add_title(*title)

        # Keep this cached here, otherwise, for every page, extra queries will
        # be made.
        self._person = get_current_branch(get_default_store()).person
        self._main_address = self._person.get_main_address()
        self._company = self._person.company

    def draw_header(self, canvas):
        canvas.saveState()
        person = self._person
        main_address = self._main_address
        company = self._company

        logo_width, logo_height = self._logotype.getSize()
        header_y = self._topMargin - logo_height - BaseStoqReport.logo_border
        header_x = self.leftMargin + BaseStoqReport.logo_border
        canvas.drawImage(self._logotype, header_x, header_y, logo_width,
                         logo_height)

        canvas.setFont(*FANCYNAME_FONT)
        text_x = header_x + logo_width + BaseStoqReport.logo_border
        text_y = header_y + logo_height - BaseStoqReport.logo_border
        if not person.name:
            raise DatabaseInconsistency("The person by ID %d should have a "
                                        "name at this point" % person.id)
        canvas.drawString(text_x, text_y, person.name)

        canvas.setFont(*SMALL_FONT)

        # Address lines
        address_string1 = ''

        address_parts = []
        if main_address:
            address_string1 = main_address.get_address_string()

            if main_address.postal_code:
                address_parts.append(main_address.postal_code)
            if main_address.get_city():
                address_parts.append(main_address.get_city())
            if main_address.get_state():
                address_parts.append(main_address.get_state())

        address_string2 = " - ".join(address_parts)

        # Contact line
        contact_parts = []
        if person.phone_number:
            contact_parts.append(_("Phone: %s")
                                   % format_phone_number(person.phone_number))
        if person.fax_number:
            contact_parts.append(_("Fax: %s")
                                   % format_phone_number(person.fax_number))

        contact_string = ' - '.join(contact_parts)

        # Company details line
        company_parts = []
        if company:
            if company.get_cnpj_number():
                company_parts.append(_("CNPJ: %s") % company.cnpj)
            if company.get_state_registry_number():
                company_parts.append(_("State Registry: %s")
                                       % company.state_registry)

        company_details_string = ' - '.join(company_parts)

        for text in (address_string1, address_string2, contact_string,
                     company_details_string):
            text_y -= TEXT_HEIGHT
            canvas.drawString(text_x, text_y, text)
        canvas.restoreState()

    #
    # Hooks
    #

    def _initialize(self):
        pass

    def get_title(self):
        raise NotImplementedError

    def get_username(self):
        user = get_current_user(get_default_store())
        return user.person.name[:45]
