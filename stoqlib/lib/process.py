# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source
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

"""Platform abstracted Process utilitites"""

import platform
import subprocess
import sys

PIPE = subprocess.PIPE


class Process(subprocess.Popen):
    def __init__(self, args, bufsize=0, executable=None, stdin=None,
                 stdout=None, stderr=None, shell=False, cwd=None, env=None,
                 quiet=True):

        if quiet and platform.system() == 'Windows':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
            # Workaround for problem described here:
            # http://www.py2exe.org/index.cgi/Py2ExeSubprocessInteractions
            # http://bytes.com/topic/python/answers/634409-subprocess-handle-invalid-error
            #
            # Basically, py2exe apps have no parent process, so they cant inherit
            # the parent handles (for stdin, stdout and stderr). In this case,
            # we must always pipe all those handles (if the call site didn't
            # already)
            if hasattr(sys, 'frozen'):
                if stdout is None:
                    stdout = PIPE
                if stderr is None:
                    stderr = PIPE
                if stdin is None:
                    stdin = PIPE
        else:
            startupinfo = None

        subprocess.Popen.__init__(self, args, bufsize, executable, stdin=stdin,
                                  stdout=stdout, stderr=stderr, shell=shell, cwd=cwd,
                                  env=env, startupinfo=startupinfo)
