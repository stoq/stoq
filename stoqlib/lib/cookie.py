# -*- Mode: Python; coding: utf-8 -*-
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

""" Simple Base64 ICookieFile implementation """

import binascii
import logging
import os

from zope.interface import implementer

from stoqlib.lib.interfaces import CookieError, ICookieFile

log = logging.getLogger(__name__)


@implementer(ICookieFile)
class Base64CookieFile(object):

    def __init__(self, filename):
        self._filename = filename

    def get(self):
        if not os.path.exists(self._filename):
            raise CookieError("%s does not exist" % self._filename)

        cookiedata = open(self._filename).read()
        if not ':' in cookiedata:
            log.info("invalid cookie file")
            raise CookieError("%s is invalid" % self._filename)

        data = cookiedata.split(":", 1)
        try:
            return (unicode(data[0]), unicode(binascii.a2b_base64(data[1])))
        except binascii.Error:
            raise CookieError("invalid format")

    def clear(self):
        try:
            os.remove(self._filename)
            log.info("Removed cookie %s" % self._filename)
        except OSError as e:
            log.info("Could not remove file %s: %r" % (self._filename, e))

    def store(self, username, password):
        if not username:
            raise CookieError("a username is required")

        try:
            fd = open(self._filename, "w")
        except IOError as e:
            raise CookieError("Could open file %s: %r" % (
                self._filename, e))

        # obfuscate password to avoid it being easily identified when
        # editing file on screen. this is *NOT* encryption!
        fd.write("%s:%s" % (username, binascii.b2a_base64(password or '')))
        fd.close()

        log.info("Saved cookie %s" % self._filename)
