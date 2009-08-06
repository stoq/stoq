# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s):   George Y. Kussumoto     <george@async.com.br>
##

import os.path
import sys

from lxml import etree
from lxml.etree import DocumentInvalid

#
# Globals
#

SCHEMAS = {'nfe': 'templates/nfe_v1.10.xsd',}

#
# Functions
#

def validate_xml(xmlfile, schema):
    nfe_schema = open(SCHEMAS[schema], 'r')
    xml_schema = etree.XMLSchema(etree.parse(nfe_schema))
    nfe_schema.close()

    xml_file = open(xmlfile, 'r')
    content = etree.parse(xml_file)

    try:
        xml_schema.assertValid(content)
    except DocumentInvalid as e:
        print '\n%s\n' % e
        return
    finally:
        xml_file.close()

    print '%s: succesfull validated' % xmlfile

def main(args):
    if len(args) != 2:
        print '%s [xml file for validation]' % args[0]
        return 1

    xml = args[1]
    if not os.path.isfile(xml):
        print 'File not found: %s' % xml
        return 1

    validate_xml(xml, 'nfe')


if __name__ == '__main__':
    sys.exit(main(sys.argv))
