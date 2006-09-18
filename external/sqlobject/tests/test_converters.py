from sqlobject.sqlbuilder import sqlrepr, TRUE, FALSE
from sqlobject.sqlbuilder import SQLExpression, SQLObjectField, \
     Select, Insert, Update, Delete, Replace, \
     SQLTrueClauseClass, SQLConstant, SQLPrefix, SQLCall, SQLOp
from sqlobject.converters import registerConverter

class TestClass:

    def __repr__(self):
        return '<TestClass>'

def TestClassConverter(value, db):
    return repr(value)

registerConverter(TestClass, TestClassConverter)

class NewTestClass:

    __metaclass__ = type

    def __repr__(self):
        return '<NewTestClass>'

def NewTestClassConverter(value, db):
    return repr(value)

registerConverter(NewTestClass, NewTestClassConverter)

def _sqlrepr(self, db):
    return '<%s>' % self.__class__.__name__

SQLExpression.__sqlrepr__ = _sqlrepr

############################################################
## Tests
############################################################

def test_simple_string():
    assert sqlrepr('A String', 'firebird') == "'A String'"

def test_string_newline():
    assert sqlrepr('A String\nAnother', 'postgres') == "'A String\\nAnother'"
    assert sqlrepr('A String\nAnother', 'sqlite') == "'A String\nAnother'"

def test_string_tab():
    assert sqlrepr('A String\tAnother', 'postgres') == "'A String\\tAnother'"

def test_string_r():
    assert sqlrepr('A String\rAnother', 'postgres') == "'A String\\rAnother'"

def test_string_b():
    assert sqlrepr('A String\bAnother', 'postgres') == "'A String\\bAnother'"

def test_string_000():
    assert sqlrepr('A String\000Another', 'postgres') == "'A String\\0Another'"

def test_string_():
    assert sqlrepr('A String\'Another', 'postgres') == "'A String\\'Another'"
    assert sqlrepr('A String\'Another', 'firebird') == "'A String''Another'"

def test_simple_unicode():
    assert sqlrepr(u'A String', 'postgres') == "'A String'"

def test_integer():
    assert sqlrepr(10) == "10"

def test_float():
    assert sqlrepr(10.01) == "10.01"

def test_none():
    assert sqlrepr(None) == "NULL"

def test_list():
    assert sqlrepr(['one','two','three'], 'postgres') == "('one', 'two', 'three')"

def test_tuple():
    assert sqlrepr(('one','two','three'), 'postgres') == "('one', 'two', 'three')"

def test_bool():
    assert sqlrepr(TRUE, 'postgres') == "'t'"
    assert sqlrepr(FALSE, 'postgres') == "'f'"
    assert sqlrepr(TRUE, 'mysql') == "1"
    assert sqlrepr(FALSE, 'mysql') == "0"

def test_datetime():
    from datetime import datetime, date, time
    assert sqlrepr(datetime(2005, 7, 14, 13, 31, 2)) == "'2005-07-14 13:31:02'"
    assert sqlrepr(date(2005, 7, 14)) == "'2005-07-14'"
    assert sqlrepr(time(13, 31, 2)) == "'13:31:02'"
    # now dates before 1900
    assert sqlrepr(datetime(1428, 7, 14, 13, 31, 2)) == "'1428-07-14 13:31:02'"
    assert sqlrepr(date(1428, 7, 14)) == "'1428-07-14'"

def test_instance():
    instance = TestClass()
    assert sqlrepr(instance) == repr(instance)

def test_newstyle():
    instance = NewTestClass()
    assert sqlrepr(instance) == repr(instance)

def test_sqlexpr():
    instance = SQLExpression()
    assert sqlrepr(instance) == repr(instance)

def test_sqlobjectfield():
    instance = SQLObjectField('test', 'test', 'test')
    assert sqlrepr(instance) == repr(instance)

def test_select():
    instance = Select('test')
    assert sqlrepr(instance, 'mysql') == "SELECT 'test'"

def test_insert():
    instance = Insert('test', [('test',)])
    assert sqlrepr(instance, 'mysql') == "INSERT INTO test VALUES ('test')"

def test_update():
    instance = Update('test', {'test':'test'})
    assert sqlrepr(instance, 'mysql') == "UPDATE test SET test='test'"

def test_delete():
    instance = Delete('test', None)
    assert sqlrepr(instance, 'mysql') == "DELETE FROM test"

def test_replace():
    instance = Replace('test', {'test':'test'})
    assert sqlrepr(instance, 'mysql') == "REPLACE test SET test='test'"

def test_trueclause():
    instance = SQLTrueClauseClass()
    assert sqlrepr(instance) == repr(instance)

def test_op():
    instance = SQLOp('and', 'this', 'that')
    assert sqlrepr(instance, 'mysql') == "('this' AND 'that')"

def test_call():
    instance = SQLCall('test', ('test',))
    assert sqlrepr(instance, 'mysql') == "'test'('test')"

def test_constant():
    instance = SQLConstant('test')
    assert sqlrepr(instance) == repr(instance)

def test_prefix():
    instance = SQLPrefix('test', 'test')
    assert sqlrepr(instance, 'mysql') == "test 'test'"
