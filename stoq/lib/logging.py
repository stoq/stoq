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

import errno
import os
import sys
import platform

def setup_logging(appname):
    """Overrides sys.stdout/sys.stderr and writes it to a file,
    this is necessary on windows got get any output from an application
    which isn't a "console" application."""
    if platform.system() != 'Windows':
        return
    logdir = os.path.join(os.environ['APPDATA'], appname, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    # http://www.py2exe.org/index.cgi/StderrLog
    for name in ['stdout', 'stderr']:
        filename = os.path.join(logdir, name + ".log")
        try:
            fp = open(filename, "w")
        except IOError, e:
            if e.errno != errno.EACCES:
                raise
            fp = open(os.devnull, "w")
        setattr(sys, name, fp)

