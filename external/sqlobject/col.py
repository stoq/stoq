"""
Col -- SQLObject columns

Note that each column object is named BlahBlahCol, and these are used
in class definitions.  But there's also a corresponding SOBlahBlahCol
object, which is used in SQLObject *classes*.

An explanation: when a SQLObject subclass is created, the metaclass
looks through your class definition for any subclasses of Col.  It
collects them together, and indexes them to do all the database stuff
you like, like the magic attributes and whatnot.  It then asks the Col
object to create an SOCol object (usually a subclass, actually).  The
SOCol object contains all the interesting logic, as well as a record
of the attribute name you used and the class it is bound to (set by
the metaclass).

So, in summary: Col objects are what you define, but SOCol objects
are what gets used.
"""

import re, time
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sqlbuilder
# Sadly the name "constraints" conflicts with many of the function
# arguments in this module, so we rename it:
import constraints as consts
from formencode import compound
from formencode import validators
from classregistry import findClass
from converters import array_type, buffer_type
from util.backports import count

NoDefault = sqlbuilder.NoDefault
True, False = 1==1, 0==1

try:
    import datetime
except ImportError: # Python 2.2
    datetime_available = False
else:
    datetime_available = True

try:
    from mx import DateTime
except ImportError:
    try:
        import DateTime # old version of mxDateTime
    except ImportError:
        mxdatetime_available = False
    else:
        mxdatetime_available = True
else:
    mxdatetime_available = True

DATETIME_IMPLEMENTATION = "datetime"
MXDATETIME_IMPLEMENTATION = "mxDateTime"

if mxdatetime_available:
    DateTimeType = type(DateTime.now())
    TimeType = type(DateTime.Time())

if datetime_available:
    default_datetime_implementation = DATETIME_IMPLEMENTATION
elif mxdatetime_available:
    default_datetime_implementation = MXDATETIME_IMPLEMENTATION
else:
    default_datetime_implementation = None

__all__ = ["datetime_available", "mxdatetime_available",
    "default_datetime_implementation"
]
if datetime_available:
    __all__.append("DATETIME_IMPLEMENTATION")
if mxdatetime_available:
    __all__.append("MXDATETIME_IMPLEMENTATION")


creationOrder = count()

class SQLValidator(compound.All):
    def attemptConvert(self, value, state, validate):
        if validate is validators.to_python:
            vlist = list(self.validators[:])
            vlist.reverse()
        elif validate is validators.from_python:
            vlist = self.validators
        else:
            raise RuntimeError
        for validator in vlist:
            value = validate(validator, value, state)
        return value


########################################
## Columns
########################################

# Col is essentially a column definition, it doesn't have
# much logic to it.
class SOCol(object):

    def __init__(self,
                 name,
                 soClass,
                 creationOrder,
                 dbName=None,
                 default=NoDefault,
                 foreignKey=None,
                 alternateID=False,
                 alternateMethodName=None,
                 constraints=None,
                 notNull=NoDefault,
                 notNone=NoDefault,
                 unique=NoDefault,
                 sqlType=None,
                 columnDef=None,
                 validator=None,
                 immutable=False,
                 cascade=None,
                 lazy=False,
                 noCache=False,
                 forceDBName=False,
                 title=None,
                 tags=[],
                 origName=None,
                 extra_vars=None):

        super(SOCol, self).__init__()

        # This isn't strictly true, since we *could* use backquotes or
        # " or something (database-specific) around column names, but
        # why would anyone *want* to use a name like that?
        # @@: I suppose we could actually add backquotes to the
        # dbName if we needed to...
        if not forceDBName:
            assert sqlbuilder.sqlIdentifier(name), 'Name must be SQL-safe (letters, numbers, underscores): %s (or use forceDBName=True)' \
               % repr(name)
        assert name != 'id', 'The column name "id" is reserved for SQLObject use (and is implicitly created).'
        assert name, "You must provide a name for all columns"

        self.columnDef = columnDef
        self.creationOrder = creationOrder

        self.immutable = immutable

        # cascade can be one of:
        # None: no constraint is generated
        # True: a CASCADE constraint is generated
        # False: a RESTRICT constraint is generated
        # 'null': a SET NULL trigger is generated
        if isinstance(cascade, str):
            assert cascade == 'null', (
                "The only string value allowed for cascade is 'null' (you gave: %r)" % cascade)
        self.cascade = cascade

        if type(constraints) not in (type([]), type(())):
            constraints = [constraints]
        self.constraints = self.autoConstraints() + constraints

        self.notNone = False
        if notNull is not NoDefault:
            self.notNone = notNull
            assert notNone is NoDefault or \
                   (not notNone) == (not notNull), \
                   "The notNull and notNone arguments are aliases, and must not conflict.  You gave notNull=%r, notNone=%r" % (notNull, notNone)
        elif notNone is not NoDefault:
            self.notNone = notNone
        if self.notNone:
            self.constraints = [consts.notNull] + self.constraints

        self.name = name
        self.soClass = soClass
        self._default = default
        self.customSQLType = sqlType

        self.foreignKey = foreignKey
        if self.foreignKey:
            #assert self.name.upper().endswith('ID'), "All foreign key columns must end with 'ID' (%s)" % repr(self.name)
            if not self.name.upper().endswith('ID'):
                self.foreignName = self.name
                self.name = self.name + "ID"
            else:
                self.foreignName = self.name[:-2]
        else:
            self.foreignName = None

        # if they don't give us a specific database name for
        # the column, we separate the mixedCase into mixed_case
        # and assume that.
        if dbName is None:
            self.dbName = soClass.sqlmeta.style.pythonAttrToDBColumn(self.name)
        else:
            self.dbName = dbName

        # alternateID means that this is a unique column that
        # can be used to identify rows
        self.alternateID = alternateID
        if self.alternateID and alternateMethodName is None:
            self.alternateMethodName = 'by' + self.name[0].capitalize() + self.name[1:]
        else:
            self.alternateMethodName = alternateMethodName

        if unique is NoDefault:
            self.unique = alternateID
        else:
            self.unique = unique

        _validators = self.createValidators()
        if _validators:
            if validator: _validators.append(validator)
            self.validator = SQLValidator.join(_validators[0], *_validators[1:])
        else:
            self.validator = validator
        self.noCache = noCache
        self.lazy = lazy
        # this is in case of ForeignKey, where we rename the column
        # and append an ID
        self.origName = origName or name
        self.title = title
        self.tags = tags

        if extra_vars:
            for name, value in extra_vars.items():
                setattr(self, name, value)

    def _set_validator(self, value):
        self._validator = value
        if self._validator:
            self.to_python = self._validator.to_python
            self.from_python = self._validator.from_python
        else:
            self.to_python = None
            self.from_python = None

    def _get_validator(self):
        return self._validator

    validator = property(_get_validator, _set_validator)

    def createValidators(self):
        """Create a list of validators for the column."""
        return []

    def autoConstraints(self):
        return []

    def _get_default(self):
        # A default can be a callback or a plain value,
        # here we resolve the callback
        if self._default is NoDefault:
            return NoDefault
        elif hasattr(self._default, '__sqlrepr__'):
            return self._default
        elif callable(self._default):
            return self._default()
        else:
            return self._default
    default = property(_get_default, None, None)

    def _get_joinName(self):
        assert self.name[-2:] == 'ID'
        return self.name[:-2]
    joinName = property(_get_joinName, None, None)

    def __repr__(self):
        r = '<%s %s' % (self.__class__.__name__, self.name)
        if self.default is not NoDefault:
            r += ' default=%s' % repr(self.default)
        if self.foreignKey:
            r += ' connected to %s' % self.foreignKey
        if self.alternateID:
            r += ' alternate ID'
        if self.notNone:
            r += ' not null'
        return r + '>'

    def createSQL(self):
        return ' '.join([self._sqlType() + self._extraSQL()])

    def _extraSQL(self):
        result = []
        if self.notNone or self.alternateID:
            result.append('NOT NULL')
        if self.unique or self.alternateID:
            result.append('UNIQUE')
        return result

    def _sqlType(self):
        if self.customSQLType is None:
            raise ValueError, ("Col %s (%s) cannot be used for automatic "
                               "schema creation (too abstract)" %
                               (self.name, self.__class__))
        else:
            return self.customSQLType

    def _mysqlType(self):
        return self._sqlType()

    def _postgresType(self):
        return self._sqlType()

    def _sqliteType(self):
        # SQLite is naturally typeless, so as a fallback it uses
        # no type.
        try:
            return self._sqlType()
        except ValueError:
            return ''

    def _sybaseType(self):
        return self._sqlType()

    def _mssqlType(self):
        return self._sqlType()

    def _firebirdType(self):
        return self._sqlType()

    def _maxdbType(self):
        return self._sqlType()

    def mysqlCreateSQL(self):
        return ' '.join([self.dbName, self._mysqlType()] + self._extraSQL())

    def postgresCreateSQL(self):
        return ' '.join([self.dbName, self._postgresType()] + self._extraSQL())

    def sqliteCreateSQL(self):
        return ' '.join([self.dbName, self._sqliteType()] + self._extraSQL())

    def sybaseCreateSQL(self):
        return ' '.join([self.dbName, self._sybaseType()] + self._extraSQL())

    def mssqlCreateSQL(self):
        return ' '.join([self.dbName, self._mssqlType()] + self._extraSQL())

    def firebirdCreateSQL(self):
        # Ian Sparks pointed out that fb is picky about the order
        # of the NOT NULL clause in a create statement.  So, we handle
        # them differently for Enum columns.
        if not isinstance(self, SOEnumCol):
            return ' '.join([self.dbName, self._firebirdType()] + self._extraSQL())
        else:
            return ' '.join([self.dbName] + [self._firebirdType()[0]] + self._extraSQL() + [self._firebirdType()[1]])

    def maxdbCreateSQL(self):
       return ' '.join([self.dbName, self._maxdbType()] + self._extraSQL())

    def __get__(self, obj, type=None):
        if obj is None:
            # class attribute, return the descriptor itself
            return self
        if obj.sqlmeta.obsolete:
            raise '@@: figure out the exception for a delete'
        if obj.sqlmeta.cacheColumns:
            columns = obj.sqlmeta._columnCache
            if columns is None:
                obj.sqlmeta.loadValues()
            try:
                return columns[name]
            except KeyError:
                return obj.sqlmeta.loadColumn(self)
        else:
            return obj.sqlmeta.loadColumn(self)

    def __set__(self, obj, value):
        if self.immutable:
            raise AttributeError("The column %s.%s is immutable" %
                                 (obj.__class__.__name__,
                                  self.name))
        obj.sqlmeta.setColumn(self, value)

    def __delete__(self, obj):
        raise AttributeError("I can't be deleted from %r" % obj)


class Col(object):

    baseClass = SOCol

    def __init__(self, name=None, **kw):
        super(Col, self).__init__()
        self.__dict__['_name'] = name
        self.__dict__['_kw'] = kw
        self.__dict__['creationOrder'] = creationOrder.next()
        self.__dict__['_extra_vars'] = {}

    def _set_name(self, value):
        assert self._name is None or self._name == value, (
            "You cannot change a name after it has already been set "
            "(from %s to %s)" % (self.name, value))
        self.__dict__['_name'] = value

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name)

    def withClass(self, soClass):
        return self.baseClass(soClass=soClass, name=self._name,
                              creationOrder=self.creationOrder,
                              columnDef=self,
                              extra_vars=self._extra_vars,
                              **self._kw)

    def __setattr__(self, var, value):
        if var == 'name':
            super(Col, self).__setattr__(var, value)
            return
        self._extra_vars[var] = value

    def __repr__(self):
        return '<%s %s %s>' % (
            self.__class__.__name__, hex(abs(id(self)))[2:],
            self._name or '(unnamed)')



class SOStringLikeCol(SOCol):
    """A common ancestor for SOStringCol and SOUnicodeCol"""
    def __init__(self, **kw):
        self.length = popKey(kw, 'length')
        self.varchar = popKey(kw, 'varchar', 'auto')
        self.char_binary = popKey(kw, 'char_binary', None) # A hack for MySQL
        if not self.length:
            assert self.varchar == 'auto' or not self.varchar, \
                   "Without a length strings are treated as TEXT, not varchar"
            self.varchar = False
        elif self.varchar == 'auto':
            self.varchar = True

        super(SOStringLikeCol, self).__init__(**kw)

    def autoConstraints(self):
        constraints = [consts.isString]
        if self.length is not None:
            constraints += [consts.MaxLength(self.length)]
        return constraints

    def _sqlType(self):
        if self.customSQLType is not None:
            return self.customSQLType
        if not self.length:
            return 'TEXT'
        elif self.varchar:
            return 'VARCHAR(%i)' % self.length
        else:
            return 'CHAR(%i)' % self.length

    def _check_case_sensitive(self, db):
        if self.char_binary:
            raise ValueError, "%s does not support binary character columns" % db

    def _mysqlType(self):
        type = self._sqlType()
        if self.char_binary:
            type += " BINARY"
        return type

    def _postgresType(self):
        self._check_case_sensitive("PostgreSQL")
        return super(SOStringLikeCol, self)._postgresType()

    def _sqliteType(self):
        self._check_case_sensitive("SQLite")
        return super(SOStringLikeCol, self)._sqliteType()

    def _sybaseType(self):
        self._check_case_sensitive("SYBASE")
        type = self._sqlType()
        if not self.notNone and not self.alternateID:
            type += ' NULL'
        return type

    def _mssqlType(self):
        if not self.length:
            type = 'varchar(4000)'
        elif self.varchar:
            type = 'VARCHAR(%i)' % self.length
        else:
            type = 'CHAR(%i)' % self.length
        if not self.notNone and not self.alternateID:
            type += ' NULL'
        return type

    def _firebirdType(self):
        self._check_case_sensitive("FireBird")
        if not self.length:
            return 'BLOB SUB_TYPE TEXT'
        else:
            return self._sqlType()

    def _maxdbType(self):
        self._check_case_sensitive("SAP DB/MaxDB")
        if not self.length:
            return 'LONG ASCII'
        else:
            return self._sqlType()


class StringValidator(validators.Validator):

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, unicode):
           return value.encode("ascii")
        return value

    def from_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, unicode):
            return value.encode("ascii")
        return value

class SOStringCol(SOStringLikeCol):

    def createValidators(self):
        return [StringValidator()] + \
            super(SOStringCol, self).createValidators()

class StringCol(Col):
    baseClass = SOStringCol

class UnicodeStringValidator(validators.Validator):

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, unicode):
            return value
        return unicode(value, self.db_encoding)

    def from_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return value.encode(self.db_encoding)

class SOUnicodeCol(SOStringLikeCol):
    def __init__(self, **kw):
        self.dbEncoding = popKey(kw, 'dbEncoding', 'UTF-8')
        super(SOUnicodeCol, self).__init__(**kw)

    def createValidators(self):
        return [UnicodeStringValidator(db_encoding=self.dbEncoding)] + \
            super(SOUnicodeCol, self).createValidators()

class UnicodeCol(Col):
    baseClass = SOUnicodeCol


class IntValidator(validators.Validator):

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, (int, long, sqlbuilder.SQLExpression)):
            return value
        try:
            try:
                return int(value)
            except OverflowError: # for Python 2.2
                return long(value)
        except:
            raise validators.Invalid("expected an int in the IntCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)

    def from_python(self, value, state):
        if value is None:
            return None
        if not isinstance(value, (int, long, sqlbuilder.SQLExpression)):
            raise validators.Invalid("expected an int in the IntCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)
        return value

class SOIntCol(SOCol):
    # 3-03 @@: support precision, maybe max and min directly

    def autoConstraints(self):
        return [consts.isInt]

    def createValidators(self):
        return [IntValidator(name=self.name)] + \
            super(SOIntCol, self).createValidators()

    def _sqlType(self):
        return 'INT'

class IntCol(Col):
    baseClass = SOIntCol

class BoolValidator(validators.Validator):

    def to_python(self, value, state):
        if value is None:
            return None
        elif not value:
            return sqlbuilder.FALSE
        else:
            return sqlbuilder.TRUE

    def from_python(self, value, state):
        if value is None:
            return None
        elif value:
            return sqlbuilder.TRUE
        else:
            return sqlbuilder.FALSE

class SOBoolCol(SOCol):
    def autoConstraints(self):
        return [consts.isBool]

    def createValidators(self):
        return [BoolValidator()] + \
            super(SOBoolCol, self).createValidators()

    def _postgresType(self):
        return 'BOOL'

    def _mysqlType(self):
        return "TINYINT"

    def _sybaseType(self):
        return "BIT"

    def _mssqlType(self):
        return "BIT"

    def _firebirdType(self):
        return 'INT'

    def _maxdbType(self):
        return "BOOLEAN"

    def _sqliteType(self):
        return "TINYINT"

class BoolCol(Col):
    baseClass = SOBoolCol


class FloatValidator(validators.Validator):

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, (int, long, float, sqlbuilder.SQLExpression)):
            return value
        try:
            return float(value)
        except:
            raise validators.Invalid("expected a float in the FloatCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)

    def from_python(self, value, state):
        if value is None:
            return None
        if not isinstance(value, (int, long, float, sqlbuilder.SQLExpression)):
            raise validators.Invalid("expected a float in the FloatCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)
        return value

class SOFloatCol(SOCol):
    # 3-03 @@: support precision (e.g., DECIMAL)

    def autoConstraints(self):
        return [consts.isFloat]

    def createValidators(self):
        return [FloatValidator(name=self.name)] + \
            super(SOFloatCol, self).createValidators()

    def _sqlType(self):
        return 'FLOAT'

    def _mysqlType(self):
        return "DOUBLE PRECISION"

class FloatCol(Col):
    baseClass = SOFloatCol


class SOKeyCol(SOCol):
    key_type = {int: "INT", str: "TEXT"}

    # 3-03 @@: this should have a simplified constructor
    # Should provide foreign key information for other DBs.

    def _sqlType(self):
        return self.key_type[self.soClass.sqlmeta.idType]

    def _sybaseType(self):
        key_type = {int: "NUMERIC(18,0) NULL", str: "TEXT"}
        return key_type[self.soClass.sqlmeta.idType]

    def _mssqlType(self):
        key_type = {int: "INT NULL", str: "TEXT"}
        return key_type[self.soClass.sqlmeta.idType]

class KeyCol(Col):

    baseClass = SOKeyCol

class SOForeignKey(SOKeyCol):

    def __init__(self, **kw):
        foreignKey = kw['foreignKey']
        style = kw['soClass'].sqlmeta.style
        if not kw.get('name'):
            kw['name'] = style.instanceAttrToIDAttr(style.pythonClassToAttr(foreignKey))
        else:
            kw['origName'] = kw['name']
            if not kw['name'].upper().endswith('ID'):
                kw['name'] = style.instanceAttrToIDAttr(kw['name'])
        super(SOForeignKey, self).__init__(**kw)

    def postgresCreateSQL(self):
        sql = SOKeyCol.postgresCreateSQL(self)
        return sql

    def postgresCreateReferenceConstraint(self):
        sTName = self.soClass.sqlmeta.table
        other = findClass(self.foreignKey, self.soClass.sqlmeta.registry)
        tName = other.sqlmeta.table
        idName = other.sqlmeta.idName
        if self.cascade is not None:
            if self.cascade == 'null':
                action = 'ON DELETE SET NULL'
            elif self.cascade:
                action = 'ON DELETE CASCADE'
            else:
                action = 'ON DELETE RESTRICT'
        else:
            action = ''
        constraint = ('ALTER TABLE %(sTName)s ADD CONSTRAINT %(colName)s_exists '
                      'FOREIGN KEY (%(colName)s) '
                      'REFERENCES %(tName)s (%(idName)s) '
                      '%(action)s' %
                      {'tName': tName,
                       'colName': self.dbName,
                       'idName': idName,
                       'action': action,
                       'sTName': sTName})
        return constraint

    def mysqlCreateReferenceConstraint(self):
        sTName = self.soClass.sqlmeta.table
        other = findClass(self.foreignKey, self.soClass.sqlmeta.registry)
        tName = other.sqlmeta.table
        idName = other.sqlmeta.idName
        if self.cascade is not None:
            if self.cascade == 'null':
                action = 'ON DELETE SET NULL'
            elif self.cascade:
                action = 'ON DELETE CASCADE'
            else:
                action = 'ON DELETE RESTRICT'
        else:
            action = ''
        constraint = ('ALTER TABLE %(sTName)s ADD CONSTRAINT %(sTName)s_%(colName)s_exists '
                      'FOREIGN KEY (%(colName)s) '
                      'REFERENCES %(tName)s (%(idName)s) '
                      '%(action)s' %
                      {'tName': tName,
                       'colName': self.dbName,
                       'idName': idName,
                       'action': action,
                       'sTName': sTName})
        return constraint

    def mysqlCreateReferenceConstraint(self):
        sTName = self.soClass.sqlmeta.table
        other = findClass(self.foreignKey, self.soClass.sqlmeta.registry)
        tName = other.sqlmeta.table
        idName = other.sqlmeta.idName
        if self.cascade is not None:
            if self.cascade == 'null':
                action = 'ON DELETE SET NULL'
            elif self.cascade:
                action = 'ON DELETE CASCADE'
            else:
                action = 'ON DELETE RESTRICT'
        else:
            action = ''
        constraint = ('ALTER TABLE %(sTName)s ADD CONSTRAINT %(sTName)s_%(colName)s_to_%(tName)s '
                      'FOREIGN KEY (%(colName)s) '
                      'REFERENCES %(tName)s (%(idName)s) '
                      '%(action)s' %
                      {'tName': tName,
                       'colName': self.dbName,
                       'idName': idName,
                       'action': action,
                       'sTName': sTName})
        return constraint

    def mysqlCreateSQL(self):
        return SOKeyCol.mysqlCreateSQL(self)

    def mysqlCreateReferenceConstraint(self):
        return None

    def sybaseCreateSQL(self):
        sql = SOKeyCol.sybaseCreateSQL(self)
        other = findClass(self.foreignKey)
        tName = other.sqlmeta.table
        idName = other.sqlmeta.idName
        reference = ('REFERENCES %(tName)s(%(idName)s) ' %
                     {'tName':tName,
                      'idName':idName})
        sql = ' '.join([sql, reference])
        return sql

    def sybaseCreateReferenceConstraint(self):
        # @@: Code from above should be moved here
        return None

    def mssqlCreateSQL(self):
        sql = SOKeyCol.mssqlCreateSQL(self)
        other = findClass(self.foreignKey)
        tName = other.sqlmeta.table
        idName = other.sqlmeta.idName
        reference = ('REFERENCES %(tName)s(%(idName)s) ' %
                     {'tName':tName,
                      'idName':idName})
        sql = ' '.join([sql, reference])
        return sql

    def mssqlCreateReferenceConstraint(self):
        # @@: Code from above should be moved here
        return None

    def maxdbCreateSQL(self):
        other = findClass(self.foreignKey)
        fidName = self.dbName
        #I assume that foreign key name is identical to the id of the reference table
        sql = ' '.join([fidName, self._maxdbType()])
        tName = other.sqlmeta.table
        idName  = other.sqlmeta.idName
        sql=sql + ',' + '\n'
        sql=sql + 'FOREIGN KEY (%s) REFERENCES %s(%s)'%(fidName,tName,idName)
        return sql

    def maxdbCreateReferenceConstraint(self):
        # @@: Code from above should be moved here
        return None

class ForeignKey(KeyCol):

    baseClass = SOForeignKey

    def __init__(self, foreignKey=None, **kw):
        super(ForeignKey, self).__init__(foreignKey=foreignKey, **kw)

class SOEnumCol(SOCol):

    def __init__(self, **kw):
        self.enumValues = popKey(kw, 'enumValues', None)
        assert self.enumValues is not None, \
               'You must provide an enumValues keyword argument'
        super(SOEnumCol, self).__init__(**kw)

    def autoConstraints(self):
        return [consts.isString, consts.InList(self.enumValues)]

    def createValidators(self):
        return [EnumValidator(name = self.name, enumValues = self.enumValues)] + \
            super(SOEnumCol, self).createValidators()

    def _mysqlType(self):
        return "ENUM(%s)" % ', '.join([sqlbuilder.sqlrepr(v, 'mysql') for v in self.enumValues])

    def _postgresType(self):
        length = max(map(self._getlength, self.enumValues))
        enumValues = ', '.join([sqlbuilder.sqlrepr(v, 'postgres') for v in self.enumValues])
        checkConstraint = "CHECK (%s in (%s))" % (self.dbName, enumValues)
        return "VARCHAR(%i) %s" % (length, checkConstraint)

    def _sqliteType(self):
        return self._postgresType()

    def _sybaseType(self):
        return self._postgresType()

    def _mssqlType(self):
        return self._postgresType()

    def _firebirdType(self):
        length = max(map(self._getlength, self.enumValues))
        enumValues = ', '.join([sqlbuilder.sqlrepr(v, 'firebird') for v in self.enumValues])
        checkConstraint = "CHECK (%s in (%s))" % (self.dbName, enumValues)
        #NB. Return a tuple, not a string here
        return "VARCHAR(%i)" % (length), checkConstraint

    def _maxdbType(self):
        raise "Enum type is not supported"

    def _getlength(self, obj):
        """
        None counts as 0; everything else uses len()
        """
        if obj is None:
            return 0
        else:
            return len(obj)

class EnumValidator(validators.Validator):

    def to_python(self, value, state):
        if value in self.enumValues:
            return value
        else:
            raise validators.Invalid("expected a member of %r in the EnumCol '%s', got %r instead" % \
                                     (self.enumValues, self.name, value), value, state)

    def from_python(self, value, state):
        return self.to_python(value, state)

class EnumCol(Col):
    baseClass = SOEnumCol


if datetime_available:
    class DateTimeValidator(validators.DateValidator):
        def to_python(self, value, state):
            if value is None:
                return None
            if isinstance(value, (datetime.datetime, datetime.date, datetime.time, sqlbuilder.SQLExpression)):
                return value
            if mxdatetime_available:
                if isinstance(value, DateTimeType):
                    # convert mxDateTime instance to datetime
                    if (self.format.find("%H") >= 0) or (self.format.find("%T")) >= 0:
                        return datetime.datetime(value.year, value.month, value.day,
                            value.hour, value.minute, int(value.second))
                    else:
                        return datetime.date(value.year, value.month, value.day)
                elif isinstance(value, TimeType):
                    # convert mxTime instance to time
                    if self.format.find("%d") >= 0:
                        return datetime.timedelta(seconds=value.seconds)
                    else:
                        return datetime.time(value.hour, value.minute, int(value.second))
            try:
                stime = time.strptime(value, self.format)
            except:
                raise validators.Invalid("expected an date/time string of the '%s' format in the DateTimeCol '%s', got %s %r instead" % \
                    (self.format, self.name, type(value), value), value, state)
            return datetime.datetime(*stime[:7])

        def from_python(self, value, state):
            if value is None:
                return None
            if isinstance(value, (datetime.datetime, datetime.date, datetime.time, sqlbuilder.SQLExpression)):
                return value
            if hasattr(value, "strftime"):
                return value.strftime(self.format)
            raise validators.Invalid("expected a datetime in the DateTimeCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)

if mxdatetime_available:
    class MXDateTimeValidator(validators.DateValidator):
        def to_python(self, value, state):
            if value is None:
                return None
            if isinstance(value, (DateTimeType, TimeType, sqlbuilder.SQLExpression)):
                return value
            if datetime_available: # convert datetime instance to mxDateTime
                if isinstance(value, datetime.datetime):
                    return DateTime.DateTime(value.year, value.month, value.day,
                        value.hour, value.minute, value.second)
                elif isinstance(value, datetime.date):
                    return DateTime.Date(value.year, value.month, value.day)
                elif isinstance(value, datetime.time):
                    return DateTime.Time(value.hour, value.minute, value.second)
            try:
                stime = time.strptime(value, self.format)
            except:
                raise validators.Invalid("expected an date/time string of the '%s' format in the DateTimeCol '%s', got %s %r instead" % \
                    (self.format, self.name, type(value), value), value, state)
            return DateTime.mktime(stime)

        def from_python(self, value, state):
            if value is None:
                return None
            if isinstance(value, (DateTimeType, TimeType, sqlbuilder.SQLExpression)):
                return value
            if hasattr(value, "strftime"):
                return value.strftime(self.format)
            raise validators.Invalid("expected a mxDateTime in the DateTimeCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)

class SODateTimeCol(SOCol):
    datetimeFormat = '%Y-%m-%d %H:%M:%S'

    def __init__(self, **kw):
        datetimeFormat = popKey(kw, 'datetimeFormat')
        if datetimeFormat:
            self.datetimeFormat = datetimeFormat
        super(SODateTimeCol, self).__init__(**kw)

    def createValidators(self):
        _validators = super(SODateTimeCol, self).createValidators()
        if default_datetime_implementation == DATETIME_IMPLEMENTATION:
            validatorClass = DateTimeValidator
        elif default_datetime_implementation == MXDATETIME_IMPLEMENTATION:
            validatorClass = MXDateTimeValidator
        if default_datetime_implementation:
            _validators.insert(0, validatorClass(name=self.name, format=self.datetimeFormat))
        return _validators

    def _mysqlType(self):
        return 'DATETIME'

    def _postgresType(self):
        return 'TIMESTAMP'

    def _sybaseType(self):
        return 'DATETIME'

    def _mssqlType(self):
        return 'DATETIME'

    def _sqliteType(self):
        return 'TIMESTAMP'

    def _firebirdType(self):
        return 'TIMESTAMP'

    def _maxdbType(self):
        return 'TIMESTAMP'

class DateTimeCol(Col):
    baseClass = SODateTimeCol
    def now():
        if default_datetime_implementation == DATETIME_IMPLEMENTATION:
            return datetime.datetime.now()
        elif default_datetime_implementation == MXDATETIME_IMPLEMENTATION:
            return DateTime.now()
        else:
            assert 0, ("No datetime implementation available "
                       "(DATETIME_IMPLEMENTATION=%r)"
                       % DATETIME_IMPLEMENTATION)
    now = staticmethod(now)


if datetime_available:
    class DateValidator(DateTimeValidator):
        def to_python(self, value, state):
            if isinstance(value, datetime.date):
                return value
            value = super(DateValidator, self).to_python(value, state)
            if isinstance(value, datetime.datetime):
                value = value.date()
            return value

        from_python = to_python

class SODateCol(SOCol):
    dateFormat = '%Y-%m-%d'

    def __init__(self, **kw):
        dateFormat = popKey(kw, 'dateFormat')
        if dateFormat: self.dateFormat = dateFormat
        super(SODateCol, self).__init__(**kw)

    def createValidators(self):
        """Create a validator for the column. Can be overriden in descendants."""
        _validators = super(SODateCol, self).createValidators()
        if default_datetime_implementation == DATETIME_IMPLEMENTATION:
            validatorClass = DateValidator
        elif default_datetime_implementation == MXDATETIME_IMPLEMENTATION:
            validatorClass = MXDateTimeValidator
        if default_datetime_implementation:
            _validators.insert(0, validatorClass(name=self.name, format=self.dateFormat))
        return _validators

    def _mysqlType(self):
        return 'DATE'

    def _postgresType(self):
        return 'DATE'

    def _sybaseType(self):
        return self._postgresType()

    def _mssqlType(self):
        """
        SQL Server doesn't have  a DATE data type, to emulate we use a vc(10)
        """
        return 'VARCHAR(10)'

    def _firebirdType(self):
        return 'DATE'

    def _maxdbType(self):
        return  'DATE'

    def _sqliteType(self):
        return 'DATE'

class DateCol(Col):
    baseClass = SODateCol


if datetime_available:
    class TimeValidator(DateTimeValidator):
        def to_python(self, value, state):
            if isinstance(value, datetime.time):
                return value
            value = super(TimeValidator, self).to_python(value, state)
            if isinstance(value, datetime.datetime):
                value = value.time()
            return value

class SOTimeCol(SOCol):
    timeFormat = '%H:%M:%S'

    def __init__(self, **kw):
        timeFormat = popKey(kw, 'timeFormat')
        if timeFormat:
            self.timeFormat = timeFormat
        super(SOTimeCol, self).__init__(**kw)

    def createValidators(self):
        _validators = super(SOTimeCol, self).createValidators()
        if default_datetime_implementation == DATETIME_IMPLEMENTATION:
            validatorClass = TimeValidator
        elif default_datetime_implementation == MXDATETIME_IMPLEMENTATION:
            validatorClass = MXDateTimeValidator
        if default_datetime_implementation:
            _validators.insert(0, validatorClass(name=self.name, format=self.timeFormat))
        return _validators

    def _mysqlType(self):
        return 'TIME'

    def _postgresType(self):
        return 'TIME'

    def _sybaseType(self):
        return 'TIME'

    def _sqliteType(self):
        return 'TIME'

    def _firebirdType(self):
        return 'TIME'

    def _maxdbType(self):
        return 'TIME'

class TimeCol(Col):
    baseClass = SOTimeCol


try:
    from decimal import Decimal
except ImportError:
    Decimal = float

class DecimalValidator(validators.Validator):
    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, (int, long, Decimal, sqlbuilder.SQLExpression)):
            return value
        if isinstance(value, float):
            value = str(value)
        connection = state.soObject._connection
        if hasattr(connection, "decimalSeparator"):
            value = value.replace(connection.decimalSeparator, ".")
        try:
            return Decimal(value)
        except:
            raise validators.Invalid("expected a Decimal in the DecimalCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)

    def from_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, float):
            value = str(value)
        if isinstance(value, (str, unicode)):
            connection = state.soObject._connection
            if hasattr(connection, "decimalSeparator"):
                value = value.replace(connection.decimalSeparator, ".")
            try:
                return Decimal(value)
            except:
                raise validators.Invalid("can not parse Decimal value '%s' in the DecimalCol from '%s'" %
                    (value, getattr(state, 'soObject', '(unknown)')), value, state)
        if not isinstance(value, (int, long, Decimal, sqlbuilder.SQLExpression)):
            raise validators.Invalid("expected a decimal in the DecimalCol '%s', got %s %r instead" % \
                (self.name, type(value), value), value, state)
        return value

class SODecimalCol(SOCol):

    def __init__(self, **kw):
        self.size = popKey(kw, 'size', NoDefault)
        assert self.size is not NoDefault, \
               "You must give a size argument"
        self.precision = popKey(kw, 'precision', NoDefault)
        assert self.precision is not NoDefault, \
               "You must give a precision argument"
        super(SODecimalCol, self).__init__(**kw)

    def _sqlType(self):
        return 'DECIMAL(%i, %i)' % (self.size, self.precision)

    def createValidators(self):
        return [DecimalValidator()] + \
            super(SODecimalCol, self).createValidators()

class DecimalCol(Col):
    baseClass = SODecimalCol

class SOCurrencyCol(SODecimalCol):

    def __init__(self, **kw):
        pushKey(kw, 'size', 10)
        pushKey(kw, 'precision', 2)
        super(SOCurrencyCol, self).__init__(**kw)

class CurrencyCol(DecimalCol):
    baseClass = SOCurrencyCol


class BinaryValidator(validators.Validator):
    """
    Validator for binary types.

    We're assuming that the per-database modules provide some form
    of wrapper type for binary conversion.
    """

    _cachedValue = None

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, str):
            module = state.soObject._connection.module
            if module.__name__ in ("sqlite", "pysqlite2.dbapi2"):
                value = module.decode(value)
            return value
        if isinstance(value, (buffer_type, state.soObject._connection._binaryType)):
            cachedValue = self._cachedValue
            if cachedValue and cachedValue[1] == value:
                return cachedValue[0]
            if isinstance(value, array_type): # MySQL
                return value.tostring()
            return str(value) # buffer => string
        raise validators.Invalid("expected a string in the BLOBCol '%s', got %s %r instead" % \
            (self.name, type(value), value), value, state)

    def from_python(self, value, state):
        if value is None:
            return None
        binary = state.soObject._connection.createBinary(value)
        self._cachedValue = (value, binary)
        return binary

class SOBLOBCol(SOStringCol):
    def createValidators(self):
        return [BinaryValidator(name=self.name)] + \
            super(SOBLOBCol, self).createValidators()

    def _mysqlType(self):
        length = self.length
        varchar = self.varchar
        if length >= 2**24:
            return varchar and "LONGTEXT" or "LONGBLOB"
        if length >= 2**16:
            return varchar and "MEDIUMTEXT" or "MEDIUMBLOB"
        if length >= 2**8:
            return varchar and "TEXT" or "BLOB"
        return varchar and "TINYTEXT" or "TINYBLOB"

    def _postgresType(self):
        return 'BYTEA'

    def _mssqlType(self):
        return "IMAGE"

class BLOBCol(StringCol):
    baseClass = SOBLOBCol


class PickleValidator(BinaryValidator):
    """
    Validator for pickle types.  A pickle type is simply a binary type
    with hidden pickling, so that we can simply store any kind of
    stuff in a particular column.

    The support for this relies directly on the support for binary for
    your database.
    """

    def to_python(self, value, state):
        if value is None:
            return None
        if isinstance(value, unicode):
            value = value.encode("ascii")
        if isinstance(value, str):
            return pickle.loads(value)
        raise validators.Invalid("expected a pickle string in the PickleCol '%s', got %s %r instead" % \
            (self.name, type(value), value), value, state)

    def from_python(self, value, state):
        if value is None:
            return None
        return pickle.dumps(value)

class SOPickleCol(SOBLOBCol):

    def __init__(self, **kw):
        self.pickleProtocol = popKey(kw, 'pickleProtocol', 1)
        super(SOPickleCol, self).__init__(**kw)

    def createValidators(self):
        return [PickleValidator(
            name=self.name, pickleProtocol=self.pickleProtocol)] + \
            super(SOPickleCol, self).createValidators()

class PickleCol(BLOBCol):
    baseClass = SOPickleCol

def popKey(kw, name, default=None):
    if not kw.has_key(name):
        return default
    value = kw[name]
    del kw[name]
    return value

def pushKey(kw, name, value):
    if not kw.has_key(name):
        kw[name] = value

all = []
for key, value in globals().items():
    if isinstance(value, type) and (issubclass(value, Col) or issubclass(value, SOCol)):
        all.append(key)
__all__.extend(all)
del all
