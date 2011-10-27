#!/bin/bash
#
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##

#
# This is a script that creates a new PostgreSQL user.
# It'll be run as the default 'postgres' user and will create the username specified on the
# command line.
# The reason for doing is this is to be able to create a username that can connect to a default
# PostgreSQL installation without a modified pg_hba.conf
#

SHNAME=`basename $0`
USERNAME=$1

unset PGUSER
unset PGHOST
unset PGDATABASE

SQLQUERY="SELECT usename FROM pg_user WHERE usename = '$USERNAME';"
HASUSER=`psql -c "$SQLQUERY"|grep -c $USERNAME`
if test "$HASUSER" = "1"; then
    echo "$SHNAME: '$USERNAME' exists, making sure it can create databases"
    psql -c "ALTER USER \"$USERNAME\" CREATEDB";
else
    # Create a user which is:
    # - allowed to create new databases (-d)
    # - a superuser (-s)
    # - not allowed to create other roles (-R)
    #
    # All of the options above needs to be passed in to avoid entering
    # interactive mode for createuser.
    #
    # We're creating superusers as that's what pg_dump requires and to use
    # COPY command (when enabling nfe plugin)
    #
    echo "$SHNAME: Creating user '$USERNAME'"
    createuser -dsR "$USERNAME"
fi

exit 0
