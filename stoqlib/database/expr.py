# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

"""Database expressions.

This contains a list of expressions that are unsupported by Storm.
Most of them are specific to PostgreSQL
"""

from storm.expr import (Expr, NamedFunc, PrefixExpr, SQL,
                        compile as expr_compile,
                        is_safe_token)


class Age(NamedFunc):
    """Given two datetimes, defines how the first is older than the second"""
    # http://www.postgresql.org/docs/9.1/static/functions-datetime.html
    __slots__ = ()
    name = "AGE"


class Round(NamedFunc):
    """Rounds takes two arguments, first is numeric and second is integer,
    first one is the number to be round and the second is the
    requested precision.
    """
    # See http://www.postgresql.org/docs/8.4/static/typeconv-func.html
    __slots__ = ()
    name = "ROUND"


class Date(NamedFunc):
    """Extract the date part of a timestamp"""
    # http://www.postgresql.org/docs/8.4/static/functions-datetime.html
    # FIXME: This is actually an operator
    __slots__ = ()
    name = "DATE"


class DateTrunc(NamedFunc):
    """Truncates a part of a datetime"""
    # http://www.postgresql.org/docs/9.1/static/functions-datetime.html
    __slots__ = ()
    name = "DATE_TRUNC"


class Distinct(NamedFunc):
    # http://www.postgresql.org/docs/8.4/interactive/sql-select.html
    # FIXME: This is actually an operator
    __slots__ = ()
    name = "DISTINCT"


class Field(SQL):
    def __init__(self, table, column):
        SQL.__init__(self, '%s.%s' % (table, column))


class Interval(PrefixExpr):
    """Defines a datetime interval"""
    # http://www.postgresql.org/docs/9.1/static/functions-datetime.html
    __slots__ = ()
    prefix = "INTERVAL"


class TransactionTimestamp(NamedFunc):
    """Current date and time at the start of the current transaction"""
    # http://www.postgresql.org/docs/8.4/static/functions-datetime.html
    __slots__ = ()
    name = "TRANSACTION_TIMESTAMP"
    date = lambda: None  # pylint


class StatementTimestamp(NamedFunc):
    """Current date and time at the start of the current statement"""
    # http://www.postgresql.org/docs/8.4/static/functions-datetime.html
    __slots__ = ()
    name = "STATEMENT_TIMESTAMP"
    date = lambda: None  # pylint


class StoqNormalizeString(NamedFunc):
    """This removes accents and other modifiers from a charater,
    it's similar to NLKD normailzation in unicode, but it is run
    inside the database.

    Note, this is very slow and should be avoided.
    In the future this will be replaced by fulltext search which
    does normalization in a cheaper way.
    """
    # See functions.sql
    __slots__ = ()
    name = "stoq_normalize_string"


class Case(Expr):
    """Works like a Python's if-then-else clause.

    CASE WHEN <condition> THEN <result>
         [WHEN <condition> THEN <result>]
    END"""
    # http://www.postgresql.org/docs/9.1/static/functions-conditional.html
    # FIXME: Support several when clauses.
    __slots__ = ("condition", "result", "else_")
    prefix = "(unknown)"

    def __init__(self, condition, result, else_=None):
        self.condition = condition
        self.result = result
        self.else_ = else_


@expr_compile.when(Case)
def compile_prefix_expr(compile, expr, state):
    stmt = "CASE WHEN %s THEN %s" % (expr_compile(expr.condition, state),
                                     expr_compile(expr.result, state))
    if expr.else_:
        stmt += ' ELSE ' + expr_compile(expr.else_, state)
    stmt += ' END'
    return stmt


def is_sql_identifier(identifier):
    return (not expr_compile.is_reserved_word(identifier) and
            is_safe_token(identifier))
