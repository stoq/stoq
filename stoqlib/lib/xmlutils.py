# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015-2017 Async Open Source <http://www.async.com.br>
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

import logging
import re
from xml.sax.saxutils import escape

from lxml import etree
from kiwi.python import strip_accents

from stoqlib.lib.translation import stoqlib_gettext as _


log = logging.getLogger(__name__)


class XmlValidationException(Exception):
    pass


class BaseTag(etree.ElementBase):
    # FIXME: How are we going to handle tags with namespaces? Note that we cannot define
    # NAMESPACE = None, otherwise lxml would add an empty namespace here.
    #NAMESPACE = None

    def setup(self):
        """Setup hook for this tag.

        Subclasses can override this if they need to create children nodes, but
        they always need to return self.
        """
        return self

    def append_tag(self, tag, value, mandatory=True, cdata=False):
        if value in [None, ''] and not mandatory:
            # If the tag is not mandatory and the value is empty,
            # dont add the tag to the xml.
            return

        if cdata and value is not None:
            value = etree.CDATA(unicode(value))
        elif value is not None:
            value = escape(strip_accents(unicode(value).strip()))

        if hasattr(self, 'NAMESPACE'):
            tag = etree.SubElement(self, '{%s}%s' % (self.NAMESPACE, tag))
        else:
            tag = etree.SubElement(self, tag)

        tag.text = value

    def export(self, filename, idented=False):
        with open(filename, 'wb') as fp:
            fp.write(etree.tostring(self, pretty_print=idented))

    def validate(self, xsd_file):
        """Validates this xml against the given xsd filename.

        :raises: :exc:`XmlValidationException` if the xml is not valid
        """
        xsd = etree.XMLSchema(file=xsd_file)
        xsd.validate(self)
        errors_log = xsd.error_log

        if errors_log:
            log.warning("XML with errors")
        else:
            log.debug("XML validated")
            return

        fields = set()
        for error in xsd.error_log:
            msg = error.message
            log.error("{}: {} {} {}".format(
                error.level_name, error.line, error.column, msg))

            # Remove some useless info from the message. Maybe we should just
            # get the field name from the message and display it?
            match = re.search("'{.*}(.*)':", msg)
            groups = match.groups()
            fields.add(groups[0] if groups else msg)

        msgs = [_("{number}) {field} is invalid").format(number=i, field=f)
                for i, f in enumerate(fields, 1)]
        raise XmlValidationException('\n'.join(msgs))
