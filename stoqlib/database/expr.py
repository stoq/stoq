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

from storm.expr import (Expr, NamedFunc, PrefixExpr, SQL, ComparableExpr,
                        compile as expr_compile, FromExpr, Undef, EXPR,
                        is_safe_token, BinaryOper, SetExpr)


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


class NullIf(NamedFunc):
    """Returns null if first argument matches second argument

    e.g. NULLIF(x, '') could be written in python like (read None as NULL):

        x if x != '' else None

    """
    # See http://www.postgresql.org/docs/8.4/static/functions-conditional.html
    __slots__ = ()
    name = "NULLIF"


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


class CharLength(NamedFunc):
    """The size of the char, just like len() in python"""
    # http://www.postgresql.org/docs/8.4/static/functions-string.html
    __slots__ = ()
    name = "CHAR_LENGTH"


class LPad(NamedFunc):
    """Fill up the string to length by prepending the characters fill"""
    # http://www.postgresql.org/docs/8.4/static/functions-string.html
    __slots__ = ()
    name = "LPAD"


class SplitPart(NamedFunc):
    """Split string on delimiter and return the given field"""
    # http://www.postgresql.org/docs/8.4/static/functions-string.html
    __slots__ = ()
    name = "split_part"


class ArrayAgg(NamedFunc):
    __slots__ = ()
    name = "array_agg"


class Contains(BinaryOper):
    __slots__ = ()
    oper = " @> "


class IsContainedBy(BinaryOper):
    __slots__ = ()
    oper = " <@ "


@expr_compile.when(Contains, IsContainedBy)
def compile_contains(expr_compile, expr, state):
    # We currently support only the first argument as a list.
    expr1 = "ARRAY[%s]" % ",".join(expr_compile(i, state) for i in expr.expr1)

    return '%s%s%s' % (expr1, expr.oper,
                       expr_compile(expr.expr2, state))


class NotIn(BinaryOper):
    __slots__ = ()
    oper = " NOT IN "


@expr_compile.when(NotIn)
def compile_in(expr_compile, expr, state):
    expr1 = expr_compile(expr.expr1, state)
    state.precedence = 0  # We're forcing parenthesis here.
    return "%s %s (%s)" % (expr1, expr.oper, expr_compile(expr.expr2, state))


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


class Case(ComparableExpr):
    """Works like a Python's if-then-else clause.

    .. line-block::

        CASE WHEN <condition> THEN <result>
             [WHEN <condition> THEN <result>]
        END
    """
    # http://www.postgresql.org/docs/9.1/static/functions-conditional.html
    # FIXME: Support several when clauses.
    __slots__ = ("condition", "result", "else_")
    prefix = "(unknown)"

    def __init__(self, condition, result, else_=None):
        self.condition = condition
        self.result = result
        self.else_ = else_


@expr_compile.when(Case)
def compile_case(compile, expr, state):
    stmt = "CASE WHEN %s THEN %s" % (expr_compile(expr.condition, state),
                                     expr_compile(expr.result, state))
    if expr.else_ is not None:
        stmt += ' ELSE ' + expr_compile(expr.else_, state)
    stmt += ' END'
    return stmt


class Trim(ComparableExpr):
    """Remove the longest string containing the given characters."""
    # http://www.postgresql.org/docs/9.1/static/functions-string.html
    __slots__ = ("op", "character", "column")
    prefix = "(unknown)"

    def __init__(self, op, character, column):
        self.op = op
        self.character = character
        self.column = column


@expr_compile.when(Trim)
def compile_trim(compile, expr, state):
    return "TRIM(%s %s FROM %s)" % (
        expr.op,
        expr_compile(expr.character, state),
        expr_compile(expr.column, state))


class Concat(Expr):
    """Concatenates string together using the || operator."""
    # http://www.postgresql.org/docs/8.4/static/functions-string.html
    __slots__ = ("inputs",)
    prefix = "(unknown)"

    def __init__(self, *inputs):
        self.inputs = inputs


@expr_compile.when(Concat)
def compile_concat(compile, expr, state):
    return " || ".join(expr_compile(input_, state) for input_ in expr.inputs)


class Between(Expr):
    """Check if value is between start and end"""
    # http://www.postgresql.org/docs/9.1/static/functions-comparison.html
    __slots__ = ('value', 'start', 'end')

    def __init__(self, value, start, end):
        self.value = value
        self.start = start
        self.end = end


@expr_compile.when(Between)
def compile_between(compile, expr, state):
    return ' %s BETWEEN %s AND %s ' % (
        expr_compile(expr.value, state),
        expr_compile(expr.start, state),
        expr_compile(expr.end, state))


class GenerateSeries(FromExpr):
    __slots__ = ('start', 'end', 'step')

    def __init__(self, start, end, step=Undef):
        self.start = start
        self.end = end
        self.step = step


@expr_compile.when(GenerateSeries)
def compile_generate_series(compile, expr, state):
    state.push("context", EXPR)
    if expr.step is Undef:
        expr = 'generate_series(%s, %s)' % (expr_compile(expr.start, state),
                                            expr_compile(expr.end, state))
    else:
        expr = 'generate_series(%s, %s, %s)' % (expr_compile(expr.start, state),
                                                expr_compile(expr.end, state),
                                                expr_compile(expr.step, state))
    state.pop()
    return expr


class UnionAll(SetExpr):
    """Union all the results

    UNION is to UNION ALL what a python's set is to a list. UNION
    will remove duplicates from the resulting rows while UNION ALL
    will just join all data, making it a little bit faster but possibly
    with more rows.
    """
    __slots__ = ()
    oper = " UNION ALL "


expr_compile.set_precedence(10, UnionAll)


def is_sql_identifier(identifier):
    return (not expr_compile.is_reserved_word(identifier) and
            is_safe_token(identifier))
