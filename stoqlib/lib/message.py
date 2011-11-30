# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Notifications and messages for stoqlib applications"""

import os
import sys

from zope.interface import implements
from kiwi.component import get_utility, provide_utility
from stoqlib.lib.interfaces import ISystemNotifier
from stoqlib.lib.uptime import get_uptime


class DefaultSystemNotifier:
    implements(ISystemNotifier)

    def _msg(self, name, short, description):
        if description:
            print '%s: [%s] %s' % (name, short, description)
        else:
            print '%s: %s' % (name, short)

    def info(self, short, description):
        self._msg('INFO', short, description)

    def yesno(self, text, default=-1, *verbs):
        self._msg('YESNO (%s/%s)' % (verbs[0], verbs[1]), text, '')

    def warning(self, short, description, *args, **kwargs):
        self._msg('WARNING', short, description, *args, **kwargs)

    def error(self, short, description):
        self._msg('ERROR', short, description)

provide_utility(ISystemNotifier, DefaultSystemNotifier())


def info(short, description=None):
    sn = get_utility(ISystemNotifier)
    sn.info(short, description)


def warning(short, description=None, *args, **kwargs):
    sn = get_utility(ISystemNotifier)
    return sn.warning(short, description, *args, **kwargs)


def error(short, description=None):
    sn = get_utility(ISystemNotifier)
    sn.error(short, description)
    sys.exit(1)


def yesno(text, default=-1, *verbs):
    sn = get_utility(ISystemNotifier)
    return sn.yesno(text, default, *verbs)


def marker(msg):
    if os.environ.get('STOQ_DEBUG'):
        print '[%.3f] %s' % (get_uptime(), msg, )
