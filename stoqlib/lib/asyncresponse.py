# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" NIH variant of twisted deferred/GLibs AsyncResult """

class AsyncResponse(object):
    def __init__(self):
        self.func = None
        self.error_func = None

    def whenDone(self, func):
        self.func = func

    def ifError(self, func):
        self.error_func = func

    def done(self, *args):
        if self.func:
            self.func(self, *args)

    def error(self, *args):
        if self.error_func:
            self.error_func(self, *args)
