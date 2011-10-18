"""
SQLObject
---------

:author: Ian Bicking <ianb@colorstudy.com>

SQLObject is a object-relational mapper.  See SQLObject.html or
SQLObject.txt for more.

Modified by:

* Daniel Savard, Xsoli Inc <sqlobject xsoli.com> 7 Feb 2004
  Added support for simple table inheritance.

* Oleg Broytmann, SIA "ANK" <phd@phd.pp.ru> 3 Feb 2005
  Split inheritance support into a number of separate modules and classes -
  InheritableSQLObject at al.

* And others...

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation; either version 2.1 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
USA.
"""

import threading
import sqlbuilder
import dbconnection
import col
import styles
import types
import warnings
import joins
import index
import classregistry
import declarative
import events
from sresults import SelectResults

import sys
if sys.version_info[:3] < (2, 2, 0):
    raise ImportError, "SQLObject requires Python 2.2.0 or later"

NoDefault = sqlbuilder.NoDefault

class SQLObjectNotFound(LookupError): pass
class SQLObjectIntegrityError(Exception): pass
class SQLObjectMoreThanOneResultError(Exception): pass

True, False = 1==1, 0==1

def makeProperties(obj):
    """
    This function takes a dictionary of methods and finds
    methods named like:
    * _get_attr
    * _set_attr
    * _del_attr
    * _doc_attr
    Except for _doc_attr, these should be methods.  It
    then creates properties from these methods, like
    property(_get_attr, _set_attr, _del_attr, _doc_attr).
    Missing methods are okay.
    """

    if isinstance(obj, dict):
        def setFunc(var, value):
            obj[var] = value
        d = obj
    else:
        def setFunc(var, value):
            setattr(obj, var, value)
        d = obj.__dict__

    props = {}
    for var, value in d.items():
        if var.startswith('_set_'):
            props.setdefault(var[5:], {})['set'] = value
        elif var.startswith('_get_'):
            props.setdefault(var[5:], {})['get'] = value
        elif var.startswith('_del_'):
            props.setdefault(var[5:], {})['del'] = value
        elif var.startswith('_doc_'):
            props.setdefault(var[5:], {})['doc'] = value
    for var, setters in props.items():
        if len(setters) == 1 and setters.has_key('doc'):
            continue
        if d.has_key(var):
            if isinstance(d[var], types.MethodType) \
                   or isinstance(d[var], types.FunctionType):
                warnings.warn(
                    "I tried to set the property %r, but it was "
                    "already set, as a method (%r).  Methods have "
                    "significantly different semantics than properties, "
                    "and this may be a sign of a bug in your code."
                    % (var, d[var]))
            continue
        setFunc(var,
                property(setters.get('get'), setters.get('set'),
                         setters.get('del'), setters.get('doc')))

def unmakeProperties(obj):
    if isinstance(obj, dict):
        def delFunc(obj, var):
            del obj[var]
        d = obj
    else:
        delFunc = delattr
        d = obj.__dict__

    for var, value in d.items():
        if isinstance(value, property):
            for prop in [value.fget, value.fset, value.fdel]:
                if prop and not d.has_key(prop.__name__):
                    delFunc(obj, var)
                    break

def findDependencies(name, registry=None):
    depends = []
    for klass in classregistry.registry(registry).allClasses():
        if findDependantColumns(name, klass):
            depends.append(klass)
    return depends

def findDependantColumns(name, klass):
    depends = []
    for col in klass.sqlmeta.columnList:
        if col.foreignKey == name and col.cascade is not None:
            depends.append(col)
    return depends

def _collectAttributes(cls, new_attrs, look_for_class, delete=True,
                       set_name=False, sort=False):
    """
    Finds all attributes in `new_attrs` that are instances of
    `look_for_class`.  Returns them as a list.  If `delete` is true
    they are also removed from the `cls`.  If `set_name` is true, then
    the ``.name`` attribute is set for any matching objects.  If
    `sort` is true, then they will be sorted by ``obj.creationOrder``.
    """
    result = []
    for attr, value in new_attrs.items():
        if isinstance(value, look_for_class):
            result.append(value)
            if set_name:
                value.name = attr
            if delete:
                delattr(cls, attr)
    if sort:
        result.sort(
            lambda a, b: cmp(a.creationOrder, b.creationOrder))
    return result

class CreateNewSQLObject:
    """
    Dummy singleton to use in place of an ID, to signal we want
    a new object.
    """
    pass

class sqlmeta(object):

    """
    This object is the object we use to keep track of all sorts of
    information.  Subclasses are made for each SQLObject subclass
    (dynamically if necessary), and instances are created to go
    alongside every SQLObject instance.
    """

    table = None
    idName = None
    # This function is used to coerce IDs into the proper format,
    # so you should replace it with str, or another function, if you
    # aren't using integer IDs
    idType = int
    style = None
    lazyUpdate = False
    defaultOrder = None
    cacheValues = True
    registry = None
    fromDatabase = False
    # Default is false, but we set it to true for the *instance*
    # when necessary: (bad clever? maybe)
    expired = False

    # This is a mapping from column names to SOCol (or subclass)
    # instances:
    columns = {}
    columnList = []

    # This is a mapping from column names to Col (or subclass)
    # instances; these objects don't have the logic that the SOCol
    # objects do, and are not attached to this class closely.
    columnDefinitions = {}

    # These are lists of the join and index objects:
    joins = []
    indexes = []
    indexDefinitions = []
    joinDefinitions = []

    __metaclass__ = declarative.DeclarativeMeta

    # These attributes shouldn't be shared with superclasses:
    _unshared_attributes = ['table', 'idName', 'columns', 'childName']

    # These are internal bookkeeping attributes; the class-level
    # definition is a default for the instances, instances will
    # reset these values.

    # When an object is being created, it has an instance
    # variable _creating, which is true.  This way all the
    # setters can be captured until the object is complete,
    # and then the row is inserted into the database.  Once
    # that happens, _creating is deleted from the instance,
    # and only the class variable (which is always false) is
    # left.
    _creating = False
    _obsolete = False
    # Sometimes an intance is attached to a connection, not
    # globally available.  In that case, self.sqlmeta._perConnection
    # will be true.  It's false by default:
    _perConnection = False

    # Inheritance definitions:
    parentClass = None # A reference to the parent class
    childClasses = {} # References to child classes, keyed by childName
    childName = None # Class name for inheritance child object creation

    def __classinit__(cls, new_attrs):
        for attr in cls._unshared_attributes:
            if not new_attrs.has_key(attr):
                setattr(cls, attr, None)
        declarative.setup_attributes(cls, new_attrs)

    def __init__(self, instance):
        self.instance = instance

    def send(cls, signal, *args, **kw):
        events.send(signal, cls.soClass, *args, **kw)

    send = classmethod(send)

    def setClass(cls, soClass):
        cls.soClass = soClass
        if not cls.style:
            cls.style = styles.defaultStyle
            try:
                if cls.soClass._connection and cls.soClass._connection.style:
                    cls.style = cls.soClass._connection.style
            except AttributeError:
                pass
        if cls.table is None:
            cls.table = cls.style.pythonClassToDBTable(cls.soClass.__name__)
        if cls.idName is None:
            cls.idName = cls.style.idForTable(cls.table)

        # plainSetters are columns that haven't been overridden by the
        # user, so we can contact the database directly to set them.
        # Note that these can't set these in the SQLObject class
        # itself, because they specific to this subclass of SQLObject,
        # and cannot be shared among classes.
        cls._plainSetters = {}
        cls._plainGetters = {}
        cls._plainForeignSetters = {}
        cls._plainForeignGetters = {}
        cls._plainJoinGetters = {}
        cls._plainJoinAdders = {}
        cls._plainJoinRemovers = {}

        # This is a dictionary of columnName: columnObject
        # None of these objects can be shared with superclasses
        cls.columns = {}
        cls.columnList = []
        # These, however, can be shared:
        cls.columnDefinitions = cls.columnDefinitions.copy()
        cls.indexes = []
        cls.indexDefinitions = cls.indexDefinitions[:]
        cls.joins = []
        cls.joinDefinitions = cls.joinDefinitions[:]

    setClass = classmethod(setClass)

    ############################################################
    ## Adding special values, like columns and indexes
    ############################################################

    ########################################
    ## Column handling
    ########################################

    def addColumn(cls, columnDef, changeSchema=False, connection=None):
        post_funcs = []
        cls.send(events.AddColumnSignal, cls.soClass, connection,
                 columnDef.name, columnDef, changeSchema, post_funcs)
        sqlmeta = cls
        soClass = cls.soClass
        del cls
        column = columnDef.withClass(soClass)
        name = column.name
        assert name != 'id', (
            "The 'id' column is implicit, and should not be defined as "
            "a column")
        if name in sqlmeta.columns:
            raise KeyError(
            "The class %s.%s already has a column %r (%r), you cannot "
            "add the column %r"
            % (soClass.__module__, soClass.__name__, name,
               sqlmeta.columnDefinitions[name],
               columnDef))
        sqlmeta.columnDefinitions[name] = columnDef
        sqlmeta.columns[name] = column
        # A stable-ordered version of the list...
        sqlmeta.columnList.append(column)

        ###################################################
        # Create the getter function(s).  We'll start by
        # creating functions like _SO_get_columnName,
        # then if there's no function named _get_columnName
        # we'll alias that to _SO_get_columnName.  This
        # allows a sort of super call, even though there's
        # no superclass that defines the database access.
        if sqlmeta.cacheValues:
            # We create a method here, which is just a function
            # that takes "self" as the first argument.
            getter = eval('lambda self: self._SO_loadValue(%s)' % repr(instanceName(name)))

        else:
            # If we aren't caching values, we just call the
            # function _SO_getValue, which fetches from the
            # database.
            getter = eval('lambda self: self._SO_getValue(%s)' % repr(name))
        setattr(soClass, rawGetterName(name), getter)

        # Here if the _get_columnName method isn't in the
        # definition, we add it with the default
        # _SO_get_columnName definition.
        if not hasattr(soClass, getterName(name)) or (name == 'childName'):
            setattr(soClass, getterName(name), getter)
            sqlmeta._plainGetters[name] = 1

        #################################################
        # Create the setter function(s)
        # Much like creating the getters, we will create
        # _SO_set_columnName methods, and then alias them
        # to _set_columnName if the user hasn't defined
        # those methods themself.

        # @@: This is lame; immutable right now makes it unsettable,
        # making the table read-only
        if not column.immutable:
            # We start by just using the _SO_setValue method
            setter = eval('lambda self, val: self._SO_setValue(%s, val, self.%s, self.%s)' % (repr(name), '_SO_from_python_%s' % name, '_SO_to_python_%s' % name))
            setattr(soClass, '_SO_from_python_%s' % name, column.from_python)
            setattr(soClass, '_SO_to_python_%s' % name, column.to_python)
            setattr(soClass, rawSetterName(name), setter)
            # Then do the aliasing
            if not hasattr(soClass, setterName(name)) or (name == 'childName'):
                setattr(soClass, setterName(name), setter)
                # We keep track of setters that haven't been
                # overridden, because we can combine these
                # set columns into one SQL UPDATE query.
                sqlmeta._plainSetters[name] = 1

        ##################################################
        # Here we check if the column is a foreign key, in
        # which case we need to make another method that
        # fetches the key and constructs the sister
        # SQLObject instance.
        if column.foreignKey:

            # We go through the standard _SO_get_columnName
            # deal, except chopping off the "ID" ending since
            # we're giving the object, not the ID of the
            # object this time:
            if sqlmeta.cacheValues:
                # self._SO_class_className is a reference
                # to the class in question.
                getter = eval('lambda self: self._SO_foreignKey(self._SO_loadValue(%r), self._SO_class_%s)' % (instanceName(name), column.foreignKey))
            else:
                # Same non-caching version as above.
                getter = eval('lambda self: self._SO_foreignKey(self._SO_getValue(%s), self._SO_class_%s)' % (repr(name), column.foreignKey))
            if column.origName.upper().endswith('ID'):
                origName = column.origName[:-2]
            else:
                origName = column.origName
            setattr(soClass, rawGetterName(origName), getter)

            # And we set the _get_columnName version
            # (sans ID ending)
            if not hasattr(soClass, getterName(name)[:-2]):
                setattr(soClass, getterName(name)[:-2], getter)
                sqlmeta._plainForeignGetters[name[:-2]] = 1

            if not column.immutable:
                # The setter just gets the ID of the object,
                # and then sets the real column.
                setter = eval('lambda self, val: setattr(self, %s, self._SO_getID(val))' % (repr(name)))
                setattr(soClass, rawSetterName(name)[:-2], setter)
                if not hasattr(soClass, setterName(name)[:-2]):
                    setattr(soClass, setterName(name)[:-2], setter)
                    sqlmeta._plainForeignSetters[name[:-2]] = 1

            classregistry.registry(sqlmeta.registry).addClassCallback(
                column.foreignKey,
                lambda foreign, me, attr: setattr(me, attr, foreign),
                soClass, '_SO_class_%s' % column.foreignKey)

        if column.alternateMethodName:
            func = eval('lambda cls, val, connection=None: cls._SO_fetchAlternateID(%s, %s, val, connection=connection)' % (repr(column.name), repr(column.dbName)))
            setattr(soClass, column.alternateMethodName, classmethod(func))

        if changeSchema:
            conn = connection or soClass._connection
            conn.addColumn(sqlmeta.table, column)

        if soClass._SO_finishedClassCreation:
            makeProperties(soClass)

        for func in post_funcs:
            func(soClass, column)

    addColumn = classmethod(addColumn)

    def addColumnsFromDatabase(sqlmeta, connection=None):
        soClass = sqlmeta.soClass
        conn = connection or soClass._connection
        for columnDef in conn.columnsFromSchema(sqlmeta.table, soClass):
            if columnDef.name not in sqlmeta.columnDefinitions:
                sqlmeta.addColumn(columnDef)

    addColumnsFromDatabase = classmethod(addColumnsFromDatabase)

    def delColumn(cls, column, changeSchema=False, connection=None):
        sqlmeta = cls
        soClass = sqlmeta.soClass
        if isinstance(column, str):
            column = sqlmeta.columns[column]
        if isinstance(column, col.Col):
            for c in sqlmeta.columns.values():
                if column is c.columnDef:
                    column = c
                    break
            else:
                raise IndexError(
                    "Column with definition %r not found" % column)
        post_funcs = []
        cls.send(events.DeleteColumnSignal, connection, column.name, column,
                 post_funcs)
        name = column.name
        del sqlmeta.columns[name]
        del sqlmeta.columnDefinitions[name]
        sqlmeta.columnList.remove(column)
        delattr(soClass, rawGetterName(name))
        if sqlmeta._plainGetters.has_key(name):
            delattr(soClass, getterName(name))
        delattr(soClass, rawSetterName(name))
        if sqlmeta._plainSetters.has_key(name):
            delattr(soClass, setterName(name))
        if column.foreignKey:
            delattr(soClass, rawGetterName(name)[:-2])
            if sqlmeta._plainForeignGetters.has_key(name[:-2]):
                delattr(soClass, getterName(name)[:-2])
            delattr(soClass, rawSetterName(name)[:-2])
            if sqlmeta._plainForeignSetters.has_key(name[:-2]):
                delattr(soClass, setterName(name)[:-2])
        if column.alternateMethodName:
            delattr(soClass, column.alternateMethodName)

        if changeSchema:
            conn = connection or soClass._connection
            conn.delColumn(sqlmeta.table, column)

        if soClass._SO_finishedClassCreation:
            unmakeProperties(soClass)

        for func in post_funcs:
            func(soClass, column)

    delColumn = classmethod(delColumn)

    ########################################
    ## Join handling
    ########################################

    def addJoin(cls, joinDef):
        sqlmeta = cls
        soClass = cls.soClass
        # The name of the method we'll create.  If it's
        # automatically generated, it's generated by the
        # join class.
        join = joinDef.withClass(soClass)
        meth = join.joinMethodName

        sqlmeta.joins.append(join)
        index = len(sqlmeta.joins)-1
        if joinDef not in sqlmeta.joinDefinitions:
            sqlmeta.joinDefinitions.append(joinDef)

        # The function fetches the join by index, and
        # then lets the join object do the rest of the
        # work:
        func = eval('lambda self: self.sqlmeta.joins[%i].performJoin(self)' % index)

        # And we do the standard _SO_get_... _get_... deal
        setattr(soClass, rawGetterName(meth), func)
        if not hasattr(soClass, getterName(meth)):
            setattr(soClass, getterName(meth), func)
            sqlmeta._plainJoinGetters[meth] = 1

        # Some joins allow you to remove objects from the
        # join.
        if hasattr(join, 'remove'):
            # Again, we let it do the remove, and we do the
            # standard naming trick.
            func = eval('lambda self, obj: self.sqlmeta.joins[%i].remove(self, obj)' % index)
            setattr(soClass, '_SO_remove' + join.addRemoveName, func)
            if not hasattr(soClass, 'remove' + join.addRemoveName):
                setattr(soClass, 'remove' + join.addRemoveName, func)
                sqlmeta._plainJoinRemovers[meth] = 1

        # Some joins allow you to add objects.
        if hasattr(join, 'add'):
            # And again...
            func = eval('lambda self, obj: self.sqlmeta.joins[%i].add(self, obj)' % index)
            setattr(soClass, '_SO_add' + join.addRemoveName, func)
            if not hasattr(soClass, 'add' + join.addRemoveName):
                setattr(soClass, 'add' + join.addRemoveName, func)
                sqlmeta._plainJoinAdders[meth] = 1

        if soClass._SO_finishedClassCreation:
            makeProperties(soClass)

    addJoin = classmethod(addJoin)

    def delJoin(sqlmeta, joinDef):
        soClass = sqlmeta.soClass
        for join in sqlmeta.joins:
            # previously deleted joins will be None, so it must
            # be skipped or it'll error out on the next line.
            if join is None:
                continue
            if joinDef is join.joinDef:
                break
        else:
            raise IndexError(
                "Join %r not found in class %r (from %r)"
                % (joinDef, soClass, sqlmeta.joins))
        meth = join.joinMethodName
        sqlmeta.joinDefinitions.remove(joinDef)
        for i in range(len(sqlmeta.joins)):
            if sqlmeta.joins[i] is join:
                # Have to leave None, because we refer to joins
                # by index.
                sqlmeta.joins[i] = None
        delattr(soClass, rawGetterName(meth))
        if sqlmeta._plainJoinGetters.has_key(meth):
            delattr(soClass, getterName(meth))
        if hasattr(join, 'remove'):
            delattr(soClass, '_SO_remove' + join.addRemovePrefix)
            if sqlmeta._plainJoinRemovers.has_key(meth):
                delattr(soClass, 'remove' + join.addRemovePrefix)
        if hasattr(join, 'add'):
            delattr(soClass, '_SO_add' + join.addRemovePrefix)
            if sqlmeta._plainJoinAdders.has_key(meth):
                delattr(soClass, 'add' + join.addRemovePrefix)

        if soClass._SO_finishedClassCreation:
            unmakeProperties(soClass)

    delJoin = classmethod(delJoin)

    ########################################
    ## Indexes
    ########################################

    def addIndex(cls, indexDef):
        cls.indexDefinitions.append(indexDef)
        index = indexDef.withClass(cls.soClass)
        cls.indexes.append(index)
        setattr(cls.soClass, index.name, index)
    addIndex = classmethod(addIndex)

    ########################################
    ## Utility methods
    ########################################

    def asDict(self):
        """
        Return the object as a dictionary of columns to values.
        """
        result = {}
        for key in self.columns:
            result[key] = getattr(self.instance, key)
        result['id'] = self.instance.id
        return result

    def expireAll(sqlmeta, connection=None):
        """
        Expire all instances of this class.
        """
        soClass = sqlmeta.soClass
        connection = connection or soClass._connection
        cache_set = connection.cache
        cache_set.weakrefAll(soClass)
        for item in cache_set.getAll(soClass):
            item.expire()

    expireAll = classmethod(expireAll)

sqlhub = dbconnection.ConnectionHub()

class _sqlmeta_attr(object):

    def __init__(self, name, deprecation_level):
        self.name = name
        self.deprecation_level = deprecation_level

    def __get__(self, obj, type=None):
        if self.deprecation_level is not None:
            deprecated(
                'Use of this attribute should be replaced with '
                '.sqlmeta.%s' % self.name, level=self.deprecation_level)
        return getattr((type or obj).sqlmeta, self.name)


# @@: This should become a public interface or documented or
# something.  Turning it on gives earlier warning about things
# that will be deprecated (having this off we won't flood people
# with warnings right away).
warnings_level = 1
exception_level = None
# Current levels:
#  1) Actively deprecated in version after 0.6.1 (0.7?); removed after
#  2) Deprecated after 1 (0.8?)
#  3) Deprecated after 2 (0.9?)

def deprecated(message, level=1, stacklevel=2):
    if exception_level is not None and exception_level <= level:
        raise NotImplementedError(message)
    if warnings_level is not None and warnings_level <= level:
        warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)

def setDeprecationLevel(warning=1, exception=None):
    """
    Set the deprecation level for SQLObject.  Low levels are more
    actively being deprecated.  Any warning at a level at or below
    ``warning`` will give a warning.  Any warning at a level at or
    below ``exception`` will give an exception.  You can use a higher
    ``exception`` level for tests to help upgrade your code.  ``None``
    for either value means never warn or raise exceptions.

    The levels currently mean:

      1) Deprecated in current version (0.7).  Will be removed in next
         version (0.8)

      2) Planned to deprecate in next version, remove later.

      3) Planned to deprecate sometime, remove sometime much later ;)

    As the SQLObject versions progress, the deprecation level of
    specific features will go down, indicating the advancing nature of
    the feature's doom.  We'll try to keep features at 1 for a major
    revision.

    As time continues there may be a level 0, which will give a useful
    error message (better than ``AttributeError``) but where the
    feature has been fully removed.
    """
    global warnings_level, exception_level
    warnings_level = warning
    exception_level = exception


# SQLObject is the superclass for all SQLObject classes, of
# course.  All the deeper magic is done in MetaSQLObject, and
# only lesser magic is done here.  All the actual work is done
# here, though -- just automatic method generation (like
# methods and properties for each column) is done in
# MetaSQLObject.
class SQLObject(object):

    __metaclass__ = declarative.DeclarativeMeta

    _connection = sqlhub

    sqlmeta = sqlmeta

    #DSM: The _inheritable attribute controls wheter the class can by
    #DSM: inherited 'logically' with a foreignKey and a back reference.
    _inheritable = False # Is this class inheritable?
    _parent = None # A reference to the parent instance
    childName = None # Children name (to be able to get a subclass)
    # moved to sqlmeta in 0.8:
    _parentClass = _sqlmeta_attr('parentClass', 2)
    _childClasses = _sqlmeta_attr('childClasses', 2)

    # The law of Demeter: the class should not call another classes by name
    SelectResultsClass = SelectResults

    def __classinit__(cls, new_attrs):

        # This is true if we're initializing the SQLObject class,
        # instead of a subclass:
        is_base = cls.__bases__ == (object,)

        cls._SO_setupSqlmeta(new_attrs, is_base)

        implicitColumns = _collectAttributes(
            cls, new_attrs, col.Col, set_name=True, sort=True)
        implicitJoins = _collectAttributes(
            cls, new_attrs, joins.Join, set_name=True)
        implicitIndexes = _collectAttributes(
            cls, new_attrs, index.DatabaseIndex, set_name=True)

        if not is_base:
            cls._SO_cleanDeprecatedAttrs(new_attrs)

        if new_attrs.has_key('_connection'):
            connection = new_attrs['_connection']
            del cls._connection
            assert not new_attrs.has_key('connection')
        elif new_attrs.has_key('connection'):
            connection = new_attrs['connection']
            del cls.connection
        else:
            connection = None

        cls._SO_finishedClassCreation = False

        if '_columns' in new_attrs and not is_base:
            deprecated(
                'The _columns attribute you gave (%r) is deprecated; '
                'columns should be added as class attributes'
                % new_attrs['_columns'], level=1)
            for column in new_attrs['_columns']:
                if isinstance(column, str):
                    column = col.Col(column)
                implicitColumns.append(column)

        if '_joins' in new_attrs and not is_base:
            deprecated(
                'The _joins attribute you gave (%r) is deprecated; '
                'joins should be added as class attributes'
                % new_attrs['_joins'], level=1)
            for j in new_attrs['_joins']:
                implicitJoins.append(j)

        ######################################################
        # Set some attributes to their defaults, if necessary.
        # First we get the connection:
        if not connection and not getattr(cls, '_connection', None):
            mod = sys.modules[cls.__module__]
            # See if there's a __connection__ global in
            # the module, use it if there is.
            if hasattr(mod, '__connection__'):
                connection = mod.__connection__

        if connection and not hasattr(cls, '_connection'):
            cls.setConnection(connection)

        # Now the class is in an essentially OK-state, so we can
        # set up any magic attributes:
        declarative.setup_attributes(cls, new_attrs)

        # We have to check if there are columns in the inherited
        # _columns where the attribute has been set to None in this
        # class.  If so, then we need to remove that column from
        # _columns.
        for key in cls.sqlmeta.columnDefinitions.keys():
            if (key in new_attrs
                and new_attrs[key] is None):
                del cls.sqlmeta.columnDefinitions[key]

        for column in cls.sqlmeta.columnDefinitions.values():
            cls.sqlmeta.addColumn(column)

        for column in implicitColumns:
            cls.sqlmeta.addColumn(column)

        if cls.sqlmeta.fromDatabase:
            cls.sqlmeta.addColumnsFromDatabase()

        for j in implicitJoins:
            cls.sqlmeta.addJoin(j)
        for i in implicitIndexes:
            cls.sqlmeta.addIndex(i)

        # We don't setup the properties until we're finished with the
        # batch adding of all the columns...
        cls._notifyFinishClassCreation()
        cls._SO_finishedClassCreation = True
        makeProperties(cls)

        # We use the magic "q" attribute for accessing lazy
        # SQL where-clause generation.  See the sql module for
        # more.
        if not is_base:
            cls.q = sqlbuilder.SQLObjectTable(cls)

        classregistry.registry(cls.sqlmeta.registry).addClass(cls)

    _style = _sqlmeta_attr('style', 2)
    _table = _sqlmeta_attr('table', 2)
    _idName = _sqlmeta_attr('idName', 2)
    _lazyUpdate = _sqlmeta_attr('lazyUpdate', 2)
    _defaultOrder = _sqlmeta_attr('defaultOrder', 2)
    _cacheValues = _sqlmeta_attr('cacheValues', 2)
    _registry = _sqlmeta_attr('registry', 2)
    _idType = _sqlmeta_attr('idType', 2)
    _fromDatabase = _sqlmeta_attr('fromDatabase', 2)
    _expired = _sqlmeta_attr('expired', 2)
    _columns = _sqlmeta_attr('columnList', 1)
    _columnDict = _sqlmeta_attr('columns', 1)
    addColumn = _sqlmeta_attr('addColumn', 2)
    delColumn = _sqlmeta_attr('delColumn', 2)
    addJoin = _sqlmeta_attr('addJoin', 2)
    delJoin = _sqlmeta_attr('delJoin', 2)
    addIndex = _sqlmeta_attr('addIndex', 2)
    delIndex = _sqlmeta_attr('delIndex', 2)
    getSchema = _sqlmeta_attr('getSchema', 2)

    # @classmethod
    def _SO_setupSqlmeta(cls, new_attrs, is_base):
        """
        This fixes up the sqlmeta attribute.  It handles both the case
        where no sqlmeta was given (in which we need to create another
        subclass), or the sqlmeta given doesn't have the proper
        inheritance.  Lastly it calls sqlmeta.setClass, which handles
        much of the setup.
        """
        if (not new_attrs.has_key('sqlmeta')
            and not is_base):
            # We have to create our own subclass, usually.
            # type(className, bases_tuple, attr_dict) creates a new
            # subclass:
            cls.sqlmeta = type('sqlmeta', (cls.sqlmeta,), {})
        if not issubclass(cls.sqlmeta, sqlmeta):
            # We allow no superclass and an object superclass, instead
            # of inheriting from sqlmeta; but in that case we replace
            # the class and just move over its attributes:
            assert cls.sqlmeta.__bases__ in ((), (object,)), (
                "If you do not inherit your sqlmeta class from "
                "sqlobject.sqlmeta, it must not inherit from any other "
                "class (your sqlmeta inherits from: %s)"
                % cls.sqlmeta.__bases__)
            for base in cls.__bases__:
                superclass = getattr(base, 'sqlmeta', None)
                if superclass:
                    break
            else:
                assert 0, (
                    "No sqlmeta class could be found in any superclass "
                    "(while fixing up sqlmeta %r inheritance)"
                    % cls.sqlmeta)
            values = dict(cls.sqlmeta.__dict__)
            for key in values.keys():
                if key.startswith('__') and key.endswith('__'):
                    # Magic values shouldn't be passed through:
                    del values[key]
            cls.sqlmeta = type('sqlmeta', (superclass,), values)

        cls.sqlmeta.setClass(cls)

    _SO_setupSqlmeta = classmethod(_SO_setupSqlmeta)

    # @classmethod
    def _SO_cleanDeprecatedAttrs(cls, new_attrs):
        """
        This removes attributes on SQLObject subclasses that have
        been deprecated; they are moved to the sqlmeta class, and
        a deprecation warning is given.
        """
        for attr in ['_table', '_lazyUpdate', '_style', '_idName',
                     '_defaultOrder', '_cacheValues', '_registry',
                     '_idType', '_fromDatabase']:
            if new_attrs.has_key(attr):
                new_name = attr[1:]
                deprecated("%r is deprecated; please set the %r "
                           "attribute in sqlmeta instead" %
                           (attr, new_name), level=2,
                           stacklevel=5)
                setattr(cls.sqlmeta, new_name, new_attrs[attr])
                delattr(cls, attr)
        for attr in ['_expired']:
            if new_attrs.has_key(attr):
                deprecated("%r is deprecated and read-only; please do "
                           "not use it in your classes until it is fully "
                           "deprecated" % attr, level=3, stacklevel=5)

    _SO_cleanDeprecatedAttrs = classmethod(_SO_cleanDeprecatedAttrs)

    def get(cls, id, connection=None, selectResults=None):

        assert id is not None, 'None is not a possible id for %s' % cls.__name__

        id = cls.sqlmeta.idType(id)

        if connection is None:
            cache = cls._connection.cache
        else:
            cache = connection.cache

        # This whole sequence comes from Cache.CacheFactory's
        # behavior, where a None returned means a cache miss.
        val = cache.get(id, cls)
        if val is None:
            try:
                val = cls(_SO_fetch_no_create=1)
                val._SO_validatorState = SQLObjectState(val)
                val._init(id, connection, selectResults)
                cache.put(id, cls, val)
            finally:
                cache.finishPut(cls)
        elif selectResults and not val.dirty:
            val._SO_writeLock.acquire()
            try:
                val._SO_selectInit(selectResults)
                val.sqlmeta.expired = False
            finally:
                val._SO_writeLock.release()
        return val

    get = classmethod(get)

    def _notifyFinishClassCreation(cls):
        pass
    _notifyFinishClassCreation = classmethod(_notifyFinishClassCreation)

    def _init(self, id, connection=None, selectResults=None):
        assert id is not None
        # This function gets called only when the object is
        # created, unlike __init__ which would be called
        # anytime the object was returned from cache.
        self.id = id
        self._SO_writeLock = threading.Lock()

        # If no connection was given, we'll inherit the class
        # instance variable which should have a _connection
        # attribute.
        if connection is not None:
            self._connection = connection
            # Sometimes we need to know if this instance is
            # global or tied to a particular connection.
            # This flag tells us that:
            self.sqlmeta._perConnection = True

        if not selectResults:
            dbNames = [col.dbName for col in self.sqlmeta.columnList]
            selectResults = self._connection._SO_selectOne(self, dbNames)
            if not selectResults:
                raise SQLObjectNotFound, "The object %s by the ID %s does not exist" % (self.__class__.__name__, self.id)
        self._SO_selectInit(selectResults)
        self._SO_createValues = {}
        self.dirty = False

    def _SO_loadValue(self, attrName):
        try:
            return getattr(self, attrName)
        except AttributeError:
            try:
                self._SO_writeLock.acquire()
                try:
                    # Maybe, just in the moment since we got the lock,
                    # some other thread did a _SO_loadValue and we
                    # have the attribute!  Let's try and find out!  We
                    # can keep trying this all day and still beat the
                    # performance on the database call (okay, we can
                    # keep trying this for a few msecs at least)...
                    result = getattr(self, attrName)
                except AttributeError:
                    pass
                else:
                    return result
                self.sqlmeta.expired = False
                dbNames = [col.dbName for col in self.sqlmeta.columnList]
                selectResults = self._connection._SO_selectOne(self, dbNames)
                if not selectResults:
                    raise SQLObjectNotFound, "The object %s by the ID %s has been deleted" % (self.__class__.__name__, self.id)
                self._SO_selectInit(selectResults)
                result = getattr(self, attrName)
                return result
            finally:
                self._SO_writeLock.release()

    def sync(self):
        if self.sqlmeta.lazyUpdate and self._SO_createValues:
            self.syncUpdate()
        self._SO_writeLock.acquire()
        try:
            dbNames = [col.dbName for col in self.sqlmeta.columnList]
            selectResults = self._connection._SO_selectOne(self, dbNames)
            if not selectResults:
                raise SQLObjectNotFound, "The object %s by the ID %s has been deleted" % (self.__class__.__name__, self.id)
            self._SO_selectInit(selectResults)
            self.sqlmeta.expired = False
        finally:
            self._SO_writeLock.release()

    def syncUpdate(self):
        if not self._SO_createValues:
            return
        self._SO_writeLock.acquire()
        try:
            if self.sqlmeta.columns:
                values = [(self.sqlmeta.columns[v[0]].dbName, v[1])
                          for v in self._SO_createValues.items()]
                self._connection._SO_update(self, values)
            self.dirty = False
            self._SO_createValues = {}
        finally:
            self._SO_writeLock.release()

    def expire(self):
        if self.sqlmeta.expired:
            return
        self._SO_writeLock.acquire()
        try:
            if self.sqlmeta.expired:
                return
            for column in self.sqlmeta.columnList:
                iname = instanceName(column.name)
                # It may be already invalidated by other callsite
                if hasattr(self, iname):
                    delattr(self, iname)
            self.sqlmeta.expired = True
            self._connection.cache.expire(self.id, self.__class__)
            self._SO_createValues = {}
        finally:
            self._SO_writeLock.release()

    def _SO_setValue(self, name, value, from_python, to_python):
        # This is the place where we actually update the
        # database.

        # If we are _creating, the object doesn't yet exist
        # in the database, and we can't insert it until all
        # the parts are set.  So we just keep them in a
        # dictionary until later:
        d = {name: value}
        if not self.sqlmeta._creating:
            self.sqlmeta.send(events.RowUpdateSignal, self, d)
        if len(d) != 1 or name not in d:
            return self.set(**d)
        value = d[name]
        if from_python:
            dbValue = from_python(value, self._SO_validatorState)
        else:
            dbValue = value
        if to_python:
            value = to_python(dbValue, self._SO_validatorState)
        if self.sqlmeta._creating or self.sqlmeta.lazyUpdate:
            self.dirty = True
            self._SO_createValues[name] = dbValue
            setattr(self, instanceName(name), value)
            return

        self._connection._SO_update(
            self, [(self.sqlmeta.columns[name].dbName,
                    dbValue)])

        if self.sqlmeta.cacheValues:
            i_name = instanceName(name)
            # This is a SQL call, meaning its value will be determined
            # only after sql execution. Invalidate cache so that the
            # actual value is reloaded
            should_invalidate = (isinstance(value, sqlbuilder.SQLCall)
                                 or self.sqlmeta.columns[name].noCache)
            if should_invalidate:
                if hasattr(self, i_name):
                    delattr(self, i_name)
            else:
                setattr(self, i_name, value)

    def set(self, **kw):
        if not self.sqlmeta._creating:
            self.sqlmeta.send(events.RowUpdateSignal, self, kw)
        # set() is used to update multiple values at once,
        # potentially with one SQL statement if possible.

        # Filter out items that don't map to column names.
        # Those will be set directly on the object using
        # setattr(obj, name, value).
        is_column = self.sqlmeta._plainSetters.has_key
        f_is_column = lambda item: is_column(item[0])
        f_not_column = lambda item: not is_column(item[0])
        items = kw.items()
        extra = dict(filter(f_not_column, items))
        kw = dict(filter(f_is_column, items))

        # _creating is special, see _SO_setValue
        if self.sqlmeta._creating or self.sqlmeta.lazyUpdate:
            for name, value in kw.items():
                from_python = getattr(self, '_SO_from_python_%s' % name, None)
                if from_python:
                    kw[name] = dbValue = from_python(value, self._SO_validatorState)
                else:
                    dbValue = value
                to_python = getattr(self, '_SO_to_python_%s' % name, None)
                if to_python:
                    value = to_python(dbValue, self._SO_validatorState)
                setattr(self, instanceName(name), value)

            self._SO_createValues.update(kw)

            for name, value in extra.items():
                try:
                    getattr(self.__class__, name)
                except AttributeError:
                    if name not in self.sqlmeta.columns:
                        raise TypeError, "%s.set() got an unexpected keyword argument %s" % (self.__class__.__name__, name)
                try:
                    setattr(self, name, value)
                except AttributeError, e:
                    raise AttributeError, '%s (with attribute %r)' % (e, name)

            self.dirty = True
            return

        self._SO_writeLock.acquire()

        try:
            # We have to go through and see if the setters are
            # "plain", that is, if the user has changed their
            # definition in any way (put in something that
            # normalizes the value or checks for consistency,
            # for instance).  If so then we have to use plain
            # old setattr() to change the value, since we can't
            # read the user's mind.  We'll combine everything
            # else into a single UPDATE, if necessary.
            toUpdate = {}
            for name, value in kw.items():
                from_python = getattr(self, '_SO_from_python_%s' % name, None)
                if from_python:
                    dbValue = from_python(value, self._SO_validatorState)
                else:
                    dbValue = value
                to_python = getattr(self, '_SO_to_python_%s' % name, None)
                if to_python:
                    value = to_python(dbValue, self._SO_validatorState)
                if self.sqlmeta.cacheValues:
                    setattr(self, instanceName(name), value)
                toUpdate[name] = dbValue
            for name, value in extra.items():
                try:
                    getattr(self.__class__, name)
                except AttributeError:
                    if name not in self.sqlmeta.columns:
                        raise TypeError, "%s.set() got an unexpected keyword argument %s" % (self.__class__.__name__, name)
                try:
                    setattr(self, name, value)
                except AttributeError, e:
                    raise AttributeError, '%s (with attribute %r)' % (e, name)

            if toUpdate:
                args = [(self.sqlmeta.columns[name].dbName, value)
                        for name, value in toUpdate.items()]
                self._connection._SO_update(self, args)
        finally:
            self._SO_writeLock.release()

    def _SO_selectInit(self, row):
        for col, colValue in zip(self.sqlmeta.columnList, row):
            if col.to_python:
                colValue = col.to_python(colValue, self._SO_validatorState)
            setattr(self, instanceName(col.name), colValue)

    def _SO_getValue(self, name):
        # Retrieves a single value from the database.  Simple.
        assert not self.sqlmeta._obsolete, (
            "%s with id %s has become obsolete" \
            % (self.__class__.__name__, self.id))
        # @@: do we really need this lock?
        #self._SO_writeLock.acquire()
        column = self.sqlmeta.columns[name]
        results = self._connection._SO_selectOne(self, [column.dbName])
        #self._SO_writeLock.release()
        assert results != None, "%s with id %s is not in the database" \
               % (self.__class__.__name__, self.id)
        value = results[0]
        if column.to_python:
            value = column.to_python(value, self._SO_validatorState)
        return value

    def _SO_foreignKey(self, id, joinClass):
        if id is None:
            return None
        elif self.sqlmeta._perConnection:
            return joinClass.get(id, connection=self._connection)
        else:
            return joinClass.get(id)

    def __init__(self, **kw):
        # We shadow the sqlmeta class with an instance of sqlmeta
        # that points to us (our sqlmeta buddy object; where the
        # sqlmeta class is our class's buddy class)
        self.sqlmeta = self.__class__.sqlmeta(self)
        # The get() classmethod/constructor uses a magic keyword
        # argument when it wants an empty object, fetched from the
        # database.  So we have nothing more to do in that case:
        if kw.has_key('_SO_fetch_no_create'):
            return

        post_funcs = []
        self.sqlmeta.send(events.RowCreateSignal, kw, post_funcs)

        # Pass the connection object along if we were given one.
        if kw.has_key('connection'):
            self._connection = kw['connection']
            self.sqlmeta._perConnection = True
            del kw['connection']

        self._SO_writeLock = threading.Lock()

        if kw.has_key('id'):
            id = self.sqlmeta.idType(kw['id'])
            del kw['id']
        else:
            id = None

        self._create(id, **kw)
        for func in post_funcs:
            func(self)

    def _create(self, id, **kw):

        self.sqlmeta._creating = True
        self._SO_createValues = {}
        self._SO_validatorState = SQLObjectState(self)

        # First we do a little fix-up on the keywords we were
        # passed:
        for column in self.sqlmeta.columnList:

            # Then we check if the column wasn't passed in, and
            # if not we try to get the default.
            if not kw.has_key(column.name) and not kw.has_key(column.foreignName):
                default = column.default

                # If we don't get it, it's an error:
                if default is NoDefault:
                    raise TypeError, "%s() did not get expected keyword argument %s" % (self.__class__.__name__, column.name)
                # Otherwise we put it in as though they did pass
                # that keyword:
                kw[column.name] = default

        self.set(**kw)

        # Then we finalize the process:
        self._SO_finishCreate(id)
        self.sqlmeta._creating = False

    def _SO_finishCreate(self, id=None):
        # Here's where an INSERT is finalized.
        # These are all the column values that were supposed
        # to be set, but were delayed until now:
        setters = self._SO_createValues.items()
        # Here's their database names:
        names = [self.sqlmeta.columns[v[0]].dbName for v in setters]
        values = [v[1] for v in setters]
        # Get rid of _SO_create*, we aren't creating anymore.
        # Doesn't have to be threadsafe because we're still in
        # new(), which doesn't need to be threadsafe.
        self.dirty = False
        if not self.sqlmeta.lazyUpdate:
            del self._SO_createValues
        else:
            self._SO_createValues = {}
        del self.sqlmeta._creating

        # Do the insert -- most of the SQL in this case is left
        # up to DBConnection, since getting a new ID is
        # non-standard.
        id = self._connection.queryInsertID(self,
                                            id, names, values)
        cache = self._connection.cache
        cache.created(id, self.__class__, self)
        self._init(id)
        post_funcs = []
        kw = dict([('class',self.__class__),('id',id)])
        self.sqlmeta.send(events.RowCreatedSignal, kw, post_funcs)


    def _SO_getID(self, obj):
        return getID(obj)

    def _findAlternateID(cls, name, dbName, value, connection=None):
        return (connection or cls._connection)._SO_selectOneAlt(
            cls,
            [cls.sqlmeta.idName] +
            [col.dbName for col in cls.sqlmeta.columnList],
            dbName,
            value), None
    _findAlternateID = classmethod(_findAlternateID)

    def _SO_fetchAlternateID(cls, name, dbName, value, connection=None, idxName=None):
        result, obj = cls._findAlternateID(name, dbName, value, connection)
        if not result:
            if idxName is None:
                raise SQLObjectNotFound, "The %s by alternateID %s = %s does not exist" % (cls.__name__, name, repr(value))
            else:
                names = []
                for i in xrange(len(name)):
                    names.append("%s = %s" % (name[i], repr(value[i])))
                names = ', '.join(names)
                raise SQLObjectNotFound, "The %s by unique index %s(%s) does not exist" % (cls.__name__, idxName, names)
        if obj:
            return obj
        if connection:
            obj = cls.get(result[0], connection=connection, selectResults=result[1:])
        else:
            obj = cls.get(result[0], selectResults=result[1:])
        return obj
    _SO_fetchAlternateID = classmethod(_SO_fetchAlternateID)

    def _SO_depends(cls):
        return findDependencies(cls.__name__, cls.sqlmeta.registry)
    _SO_depends = classmethod(_SO_depends)

    def select(cls, clause=None, clauseTables=None,
               orderBy=NoDefault, limit=None,
               lazyColumns=False, reversed=False,
               distinct=False, connection=None,
               join=None, having=None):
        return cls.SelectResultsClass(cls, clause,
                             clauseTables=clauseTables,
                             orderBy=orderBy,
                             limit=limit,
                             having=having,
                             lazyColumns=lazyColumns,
                             reversed=reversed,
                             distinct=distinct,
                             connection=connection,
                             join=join)
    select = classmethod(select)

    def selectBy(cls, connection=None, **kw):
        conn = connection or cls._connection
        return cls.SelectResultsClass(cls,
                                      conn._SO_columnClause(cls, kw),
                                      connection=conn)

    selectBy = classmethod(selectBy)

    def selectOne(cls, clause=None, clauseTables=None, lazyColumns=False,
                  connection=None):
        """A variant of select to return a single result.

        If clause finds no results, this returns None.  If it finds one result,
        it returns it.  If it finds more than one result, it raises a
        SQLObjectMoreThanOneResultError.
        """
        results = list(cls.SelectResultsClass(
            cls, clause,
            clauseTables=clauseTables,
            lazyColumns=lazyColumns,
            connection=connection).limit(2))

        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            raise SQLObjectMoreThanOneResultError(
                "%d rows retrieved by selectOne" % len(results))

    selectOne = classmethod(selectOne)

    def selectOneBy(cls, connection=None, **kw):
        """A variant of selectBy to return a single result.

        If it finds no results, this returns None.  If it finds one result,
        it returns it.  If it finds more than one result, it raises a
        SQLObjectMoreThanOneResultError.
        """
        conn = connection or cls._connection
        results = list(cls.SelectResultsClass(
            cls,
            clause=conn._SO_columnClause(cls, kw),
            connection=conn).limit(2))

        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results[0]
        else:
            raise SQLObjectMoreThanOneResultError(
                "%d rows retrieved by selectOne" % len(results))

    selectOneBy = classmethod(selectOneBy)

    def dropTable(cls, ifExists=False, dropJoinTables=True, cascade=False,
                  connection=None):
        conn = connection or cls._connection
        if ifExists and not conn.tableExists(cls.sqlmeta.table):
            return
        extra_sql = []
        post_funcs = []
        cls.sqlmeta.send(events.DropTableSignal, cls, connection,
                         extra_sql, post_funcs)
        conn.dropTable(cls.sqlmeta.table, cascade)
        if dropJoinTables:
            cls.dropJoinTables(ifExists=ifExists, connection=conn)
        for sql in extra_sql:
            connection.query(sql)
        for func in post_funcs:
            func(cls, conn)
    dropTable = classmethod(dropTable)

    def createTable(cls, ifNotExists=False, createJoinTables=True,
                    createIndexes=True, applyConstraints=True,
                    connection=None):
        conn = connection or cls._connection
        if ifNotExists and conn.tableExists(cls.sqlmeta.table):
            return
        extra_sql = []
        post_funcs = []
        cls.sqlmeta.send(events.CreateTableSignal, cls, connection,
                         extra_sql, post_funcs)
        constraints = conn.createTable(cls)
        if applyConstraints:
            for constraint in constraints:
                conn.query(constraint)
        else:
            extra_sql.extend(constraints)
        if createJoinTables:
            cls.createJoinTables(ifNotExists=ifNotExists,
                                 connection=conn)
        if createIndexes:
            cls.createIndexes(ifNotExists=ifNotExists,
                              connection=conn)
        for func in post_funcs:
            func(cls, conn)
        return extra_sql
    createTable = classmethod(createTable)

    def createTableSQL(cls, createJoinTables=True, createIndexes=True,
                       connection=None):
        conn = connection or cls._connection
        sql, constraints = conn.createTableSQL(cls)
        if createJoinTables:
            sql += '\n' + cls.createJoinTablesSQL(connection=conn)
        if createIndexes:
            sql += '\n' + cls.createIndexesSQL(connection=conn)
        return sql, constraints
    createTableSQL = classmethod(createTableSQL)

    def createJoinTables(cls, ifNotExists=False, connection=None):
        conn = connection or cls._connection
        for join in cls._getJoinsToCreate():
            if not getattr(join, 'createRelatedTable', True):
                # This join has requested not to be created
                continue
            if (ifNotExists and
                conn.tableExists(join.intermediateTable)):
                continue
            conn._SO_createJoinTable(join)
    createJoinTables = classmethod(createJoinTables)

    def createJoinTablesSQL(cls, connection=None):
        conn = connection or cls._connection
        sql = []
        for join in cls._getJoinsToCreate():
            if not getattr(join, 'createRelatedTable', True):
                # This join has requested not to be created
                continue
            sql.append(conn._SO_createJoinTableSQL(join))
        return '\n'.join(sql)
    createJoinTablesSQL = classmethod(createJoinTablesSQL)

    def createIndexes(cls, ifNotExists=False, connection=None):
        conn = connection or cls._connection
        for index in cls.sqlmeta.indexes:
            if not index:
                continue
            conn._SO_createIndex(cls, index)
    createIndexes = classmethod(createIndexes)

    def createIndexesSQL(cls, connection=None):
        conn = connection or cls._connection
        sql = []
        for index in cls.sqlmeta.indexes:
            if not index:
                continue
            sql.append(conn.createIndexSQL(cls, index))
        return '\n'.join(sql)
    createIndexesSQL = classmethod(createIndexesSQL)

    def _getJoinsToCreate(cls):
        joins = []
        for join in cls.sqlmeta.joins:
            if not join:
                continue
            if not join.hasIntermediateTable():
                continue
            if join.soClass.__name__ > join.otherClass.__name__:
                continue
            joins.append(join)
        return joins
    _getJoinsToCreate = classmethod(_getJoinsToCreate)

    def dropJoinTables(cls, ifExists=False, connection=None):
        conn = connection or cls._connection
        for join in cls.sqlmeta.joins:
            if not join:
                continue
            if not join.hasIntermediateTable():
                continue
            if join.soClass.__name__ > join.otherClass.__name__:
                continue
            if ifExists and \
               not conn.tableExists(join.intermediateTable):
                continue
            conn._SO_dropJoinTable(join)

    dropJoinTables = classmethod(dropJoinTables)

    def clearTable(cls, connection=None, clearJoinTables=True):
        # 3-03 @@: Maybe this should check the cache... but it's
        # kind of crude anyway, so...
        conn = connection or cls._connection
        conn.clearTable(cls.sqlmeta.table)
        if clearJoinTables:
            for join in cls._getJoinsToCreate():
                conn.clearTable(join.intermediateTable)
    clearTable = classmethod(clearTable)

    def destroySelf(self):
        self.sqlmeta.send(events.RowDestroySignal, self)
        # Kills this object.  Kills it dead!
        depends = []
        klass = self.__class__
        depends = self._SO_depends()
        for k in depends:
            cols = findDependantColumns(klass.__name__, k)
            query = []
            delete = setnull = restrict = False
            for col in cols:
                if col.cascade == False:
                    # Found a restriction
                    restrict = True
                query.append("%s = %s" % (col.dbName, self.id))
                if col.cascade == 'null':
                    setnull = col.name
                elif col.cascade:
                    delete = True
            assert delete or setnull or restrict, (
                "Class %s depends on %s accoriding to "
                "findDependantColumns, but this seems inaccurate"
                % (k, klass))
            query = ' OR '.join(query)
            results = k.select(query, connection=self._connection)
            if restrict:
                if results.count():
                    # Restrictions only apply if there are
                    # matching records on the related table
                    raise SQLObjectIntegrityError, (
                        "Tried to delete %s::%s but "
                        "table %s has a restriction against it" %
                        (klass.__name__, self.id, k.__name__))
            else:
                for row in results:
                    if delete:
                        row.destroySelf()
                    else:
                        row.set(**{setnull: None})

        self.sqlmeta._obsolete = True
        self._connection._SO_delete(self)
        self._connection.cache.expire(self.id, self.__class__)

    def delete(cls, id, connection=None):
        obj = cls.get(id, connection=connection)
        obj.destroySelf()

    delete = classmethod(delete)

    def __repr__(self):
        if not hasattr(self, 'id'):
            # Object initialization not finished.  No attributes can be read.
            return '<%s (not initialized)>' % self.__class__.__name__
        return '<%s %r %s>' \
               % (self.__class__.__name__,
                  self.id,
                  ' '.join(['%s=%s' % (name, repr(value)) for name, value in self._reprItems()]))

    def sqlrepr(cls, value, connection=None):
        return (connection or cls._connection).sqlrepr(value)

    sqlrepr = classmethod(sqlrepr)

    def coerceID(cls, value):
        if isinstance(value, cls):
            return value.id
        else:
            return cls.sqlmeta.idType(value)

    coerceID = classmethod(coerceID)

    def _reprItems(self):
        items = []
        for col in self.sqlmeta.columnList:
            value = getattr(self, col.name)
            r = repr(value)
            if len(r) > 20:
                value = r[:17] + "..." + r[-1]
            items.append((col.name, value))
        return items

    def setConnection(cls, value):
        if isinstance(value, (str, unicode)):
            value = dbconnection.connectionForURI(value)
        cls._connection = value
    setConnection = classmethod(setConnection)

def capitalize(name):
    return name[0].capitalize() + name[1:]

def setterName(name):
    return '_set_%s' % name
def rawSetterName(name):
    return '_SO_set_%s' % name
def getterName(name):
    return '_get_%s' % name
def rawGetterName(name):
    return '_SO_get_%s' % name
def instanceName(name):
    return '_SO_val_%s' % name


class SQLObjectState(object):

    def __init__(self, soObject):
        self.soObject = soObject
        self.protocol = 'sql'


########################################
## Utility functions (for external consumption)
########################################

def getID(obj):
    if isinstance(obj, SQLObject):
        return obj.id
    elif type(obj) is type(1):
        return obj
    elif type(obj) is type(1L):
        return int(obj)
    elif type(obj) is type(""):
        try:
            return int(obj)
        except ValueError:
            return obj
    elif obj is None:
        return None

def getObject(obj, klass):
    if type(obj) is type(1):
        return klass(obj)
    elif type(obj) is type(1L):
        return klass(int(obj))
    elif type(obj) is type(""):
        return klass(int(obj))
    elif obj is None:
        return None
    else:
        return obj

__all__ = ['NoDefault', 'SQLObject', 'sqlmeta',
           'getID', 'getObject',
           'SQLObjectNotFound', 'SQLObjectMoreThanOneResultError', 'sqlhub',
           'setDeprecationLevel']
