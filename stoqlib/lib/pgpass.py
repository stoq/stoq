# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
import logging
import os
import platform

logger = logging.getLogger(__name__)


def write_pg_pass(dbname, address, port, username, password):
    logger.info('write_pgpass')
    # There's no way to pass in the password to psql via the command line,
    # so we need to setup a pgpass where we store the password entered here
    if platform.system() == 'Windows':
        directory = os.path.join(os.environ['APPDATA'],
                                 'postgresql')
        passfile = os.path.join(directory, 'pgpass.conf')
    else:
        directory = os.environ.get('HOME', '/')
        passfile = os.path.join(directory, '.pgpass')
    pgpass = os.environ.get('PGPASSFILE', passfile)

    # FIXME: remove duplicates when trying several different passwords
    if os.path.exists(pgpass):
        with open(pgpass) as f:
            lines = [l.strip('\n') for l in f]
    else:
        lines = []

    # _get_store_internal connects to the 'postgres' database,
    # we need to allow connections without asking the password,
    # otherwise stoqdbadmin will be stuck in the wizard when creating
    # a new database.
    for dbname in ['postgres', dbname]:
        line = '%s:%s:%s:%s:%s' % (address, port, dbname, username, password)
        if line in lines:
            continue
        lines.append(line)

    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(pgpass, 'w') as fd:
        fd.write('\n'.join(lines))
        fd.write('\n')
    os.chmod(pgpass, 0600)
