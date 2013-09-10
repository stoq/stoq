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

"""socket utilities"""

import errno
import os
import random
import socket


def get_hostname():
    # For LTSP systems we cannot use the hostname as stoq is run
    # on a shared serve system. Instead the ip of the client system
    # is available in the LTSP_CLIENT environment variable
    name = os.environ.get('LTSP_CLIENT_HOSTNAME', None)
    if name is None:
        name = socket.gethostname()
    return unicode(name)


def get_random_port():
    i = 0
    while True:
        port = random.randrange(30000, 40000)
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            try:
                sockfd.bind(("", port))
                return sockfd.getsockname()[1]
            except socket.error as e:
                if e.message != errno.EADDRINUSE:
                    raise
        finally:
            sockfd.close()

        if i > 10:
            raise Exception("No port open")
        i += 1
