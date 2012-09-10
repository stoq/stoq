# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2012 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.environ import environ

from stoqlib.database.runtime import get_connection
from stoqlib.lib.template import render_template
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.template import get_logotype_path

_ = stoqlib_gettext


class HTMLReport(object):
    template_filename = None
    title = ''
    complete_header = True

    def __init__(self, filename):
        self.filename = filename
        self.logo_path = get_logotype_path(get_connection())

    def get_html(self):
        assert self.title
        namespace = self.get_namespace()
        # Set some defaults if the report did not provide one
        namespace.setdefault('subtitle', '')
        namespace.setdefault('notes', [])
        return render_template(self.template_filename,
                               title=self.title,
                               complete_header=self.complete_header,
                               logo_path=self.logo_path,
                               _=stoqlib_gettext,
                               **namespace)

    def save_html(self, filename):
        html = open(filename, 'w')
        html.write(self.get_html())
        html.flush()

    def save(self):
        import weasyprint
        template_dirs = environ.get_resource_paths('template')
        html = weasyprint.HTML(string=self.get_html(),
                               base_url=template_dirs[0])
        html.write_pdf(self.filename)

    #
    # Hook methods
    #

    def get_namespace(self):
        """This hook method must be implemented by children and returns
        parameters that will be passed to report template in form of a dict.
        """
        raise NotImplementedError

    def adjust_for_test(self):
        """This hook method must be implemented by children that generates
        reports with data that change with the workstation or point in time.
        This allows for the test reports to be always generated with the same
        data.
        """
