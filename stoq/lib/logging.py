# -*- coding: utf-8 -*-
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

import os
import time


def setup_logging(appname):
    from stoqlib.lib.osutils import get_application_dir
    stoqdir = get_application_dir(appname)

    log_dir = os.path.join(stoqdir, 'logs', time.strftime('%Y'),
                           time.strftime('%m'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    from kiwi.log import set_log_file
    _log_filename = os.path.join(log_dir, 'stoq_%s.log' %
                                time.strftime('%Y-%m-%d_%H-%M-%S'))
    _stream = set_log_file(_log_filename, 'stoq*')

    if hasattr(os, 'symlink'):
        link_file = os.path.join(stoqdir, 'stoq.log')
        if os.path.exists(link_file):
            os.unlink(link_file)
        os.symlink(_log_filename, link_file)

    return _log_filename, _stream
