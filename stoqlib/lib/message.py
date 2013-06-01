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

import logging
import os
import sys

from zope.interface import implementer
from kiwi.component import get_utility, provide_utility

from stoqlib.lib.interfaces import ISystemNotifier
from stoqlib.lib.uptime import get_uptime

log = logging.getLogger(__name__)


@implementer(ISystemNotifier)
class DefaultSystemNotifier:
    def message(self, name, short, description):
        if isinstance(short, unicode):
            short = short.encode('utf-8')
        if isinstance(description, unicode):
            description = description.encode('utf-8')

        if description:
            print('%s: [%s] %s' % (name, short, description))
        else:
            print('%s: %s' % (name, short))

    def info(self, short, description):
        self.message('INFO', short, description)

    def yesno(self, text, default=-1, *verbs):
        self.message('YESNO (%s/%s)' % (verbs[0], verbs[1]), text, '')

    def warning(self, short, description, *args, **kwargs):
        self.message('WARNING', short, description, *args, **kwargs)

    def error(self, short, description):
        self.message('ERROR', short, description)


def info(short, description=None):
    sn = get_utility(ISystemNotifier)
    log.info("Info: short='%s' description='%s'" %
             (short, description))
    sn.info(short, description)


def warning(short, description=None, *args, **kwargs):
    sn = get_utility(ISystemNotifier)
    log.info("Warning: short='%s' description='%s'" %
             (short, description))
    return sn.warning(short, description, *args, **kwargs)


def error(short, description=None):
    sn = get_utility(ISystemNotifier)
    log.info("Error: short='%s' description='%s'" %
             (short, description))
    sn.error(short, description)
    sys.exit(1)


def yesno(text, default=-1, *verbs):
    sn = get_utility(ISystemNotifier)
    rv = sn.yesno(text, default, *verbs)
    log.info("Yes/No: text='%s' verbs='%r' rv='%r'" %
             (text, verbs, rv))
    return rv


def marker(msg):
    if os.environ.get('STOQ_DEBUG'):
        sys.stderr.write('[%.3f] %s\n' % (get_uptime(), msg, ))


# During normall shell startup this is already set,
# so only install the text mode version when we starting up
# via stoqdbadmin or other ways.
if get_utility(ISystemNotifier, None) is None:
    provide_utility(ISystemNotifier, DefaultSystemNotifier())
