# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##

"""Simple ORM abstraction layer"""

from kiwi.db.sqlobj import SQLObjectQueryExecuter

from sqlobject import connectionForURI, SQLObjectNotFound, SQLObjectMoreThanOneResultError
from sqlobject.dbconnection import DBAPI, Transaction
from sqlobject.main import SQLObject
from sqlobject.sresults import SelectResults
from sqlobject.util.csvexport import export_csv
from sqlobject.viewable import Viewable



class ORMObject(SQLObject):
    pass

# ORMObject.get raises this
ORMObjectNotFound = SQLObjectNotFound
# ORMObject.selectOneBy raises this
ORMObjectMoreThanOneResultError = SQLObjectMoreThanOneResultError

ORMObjectQueryExecuter = SQLObjectQueryExecuter

connectionForURI = connectionForURI
Transaction = Transaction
DBAPI = DBAPI
SelectResults = SelectResults
export_csv = export_csv
Viewable = Viewable
