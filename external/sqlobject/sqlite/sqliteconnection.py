from sqlobject.dbconnection import DBAPI
from sqlobject.col import popKey
from sqlobject import col, sqlbuilder
from sqlobject.dberrors import *
import thread

sqlite = None
using_sqlite2 = False
sqlite2_Binary = None

class ErrorMessage(str):
    def __new__(cls, e):
        obj = str.__new__(cls, e[0])
        obj.code = None
        obj.module = e.__module__
        obj.exception = e.__class__.__name__
        return obj

class SQLiteConnection(DBAPI):

    supportTransactions = True
    dbName = 'sqlite'
    schemes = [dbName]

    def __init__(self, filename, autoCommit=1, **kw):
        global sqlite
        global using_sqlite2
        if sqlite is None:
            try:
                import sqlite3 as sqlite
                using_sqlite2 = True
            except ImportError:
                try:
                    from pysqlite2 import dbapi2 as sqlite
                    using_sqlite2 = True
                except ImportError:
                    import sqlite
                    using_sqlite2 = False
        self.module = sqlite
        self.filename = filename  # full path to sqlite-db-file
        self._memory = filename == ':memory:'
        if self._memory:
            if not using_sqlite2:
                raise ValueError(
                    "You must use sqlite2 to use in-memory databases")
        # connection options
        opts = {}
        if using_sqlite2:
            if autoCommit:
                opts["isolation_level"] = None
            if 'encoding' in kw:
                import warnings
                warnings.warn(DeprecationWarning("pysqlite2 does not support the encoding option"))
            opts["detect_types"] = sqlite.PARSE_DECLTYPES
            for col_type in "text", "char", "varchar", "date", "time", "datetime", "timestamp":
                sqlite.register_converter(col_type, stop_pysqlite2_converting_strings)
                sqlite.register_converter(col_type.upper(), stop_pysqlite2_converting_strings)
            try:
                from sqlite import encode, decode
            except ImportError:
                import base64
                sqlite.encode = base64.encodestring
                sqlite.decode = base64.decodestring
            else:
                sqlite.encode = encode
                sqlite.decode = decode
            global sqlite2_Binary
            if sqlite2_Binary is None:
                sqlite2_Binary = sqlite.Binary
                sqlite.Binary = lambda s: sqlite2_Binary(sqlite.encode(s))
            if 'factory' in kw:
                factory = popKey(kw, 'factory')
                if isinstance(factory, str):
                    factory = globals()[factory]
                opts['factory'] = factory(sqlite)
        else:
            opts['autocommit'] = bool(autoCommit)
            if 'encoding' in kw:
                opts['encoding'] = popKey(kw, 'encoding')
            if 'mode' in kw:
                opts['mode'] = int(popKey(kw, 'mode'), 0)
        if 'timeout' in kw:
            if using_sqlite2:
                opts['timeout'] = float(popKey(kw, 'timeout'))
            else:
                opts['timeout'] = int(float(popKey(kw, 'timeout')) * 1000)
        if 'check_same_thread' in kw:
            opts["check_same_thread"] = bool(popKey(kw, 'check_same_thread'))
        # use only one connection for sqlite - supports multiple)
        # cursors per connection
        self._connOptions = opts
        self.use_table_info = popKey(kw, "use_table_info", False)
        DBAPI.__init__(self, **kw)
        self._threadPool = {}
        self._threadOrigination = {}
        if self._memory:
            self._memoryConn = sqlite.connect(
                self.filename, **self._connOptions)

    def connectionFromURI(cls, uri):
        user, password, host, port, path, args = cls._parseURI(uri)
        assert host is None, (
            "SQLite can only be used locally (with a URI like "
            "sqlite:///file or sqlite:/file, not %r)" % uri)
        assert user is None and password is None, (
            "You may not provide usernames or passwords for SQLite "
            "databases")
        if path == "/:memory:":
            path = ":memory:"
        return cls(filename=path, **args)
    connectionFromURI = classmethod(connectionFromURI)

    def uri(self):
        return 'sqlite:///%s' % self.filename

    def getConnection(self):
        # SQLite can't share connections between threads, and so can't
        # pool connections.  Since we are isolating threads here, we
        # don't have to worry about locking as much.
        if self._memory:
            conn = self.makeConnection()
            self._connectionNumbers[id(conn)] = self._connectionCount
            self._connectionCount += 1
            return conn
        threadid = thread.get_ident()
        if (self._pool is not None
            and self._threadPool.has_key(threadid)):
            conn = self._threadPool[threadid]
            del self._threadPool[threadid]
            if conn in self._pool:
                self._pool.remove(conn)
        else:
            conn = self.makeConnection()
            if self._pool is not None:
                self._threadOrigination[id(conn)] = threadid
            self._connectionNumbers[id(conn)] = self._connectionCount
            self._connectionCount += 1
        if self.debug:
            s = 'ACQUIRE'
            if self._pool is not None:
                s += ' pool=[%s]' % ', '.join([str(self._connectionNumbers[id(v)]) for v in self._pool])
            self.printDebug(conn, s, 'Pool')
        return conn

    def releaseConnection(self, conn, explicit=False):
        if self._memory:
            return
        threadid = self._threadOrigination.get(id(conn))
        DBAPI.releaseConnection(self, conn, explicit=explicit)
        if (self._pool is not None and threadid
            and not self._threadPool.has_key(threadid)):
            self._threadPool[threadid] = conn
        else:
            if self._pool and conn in self._pool:
                self._pool.remove(conn)
            conn.close()

    def _setAutoCommit(self, conn, auto):
        if using_sqlite2:
            if auto:
                conn.isolation_level = None
            else:
                conn.isolation_level = ""
        else:
            conn.autocommit = auto

    def _setIsolationLevel(self, conn, level):
        if not using_sqlite2:
            return
        conn.isolation_level = level

    def makeConnection(self):
        if self._memory:
            return self._memoryConn
        return sqlite.connect(self.filename, **self._connOptions)

    def _executeRetry(self, conn, cursor, query):
        query = query.replace('NOW()', "datetime('now')")

        if self.debug:
            self.printDebug(conn, query, 'QueryR')
        try:
            return cursor.execute(query)
        except self.module.OperationalError, e:
            raise OperationalError(ErrorMessage(e))
        except self.module.IntegrityError, e:
            msg = ErrorMessage(e)
            if msg.startswith('column') and msg.endswith('not unique'):
                raise DuplicateEntryError(msg)
            else:
                raise IntegrityError(msg)
        except self.module.InternalError, e:
            raise InternalError(ErrorMessage(e))
        except self.module.ProgrammingError, e:
            raise ProgrammingError(ErrorMessage(e))
        except self.module.DataError, e:
            raise DataError(ErrorMessage(e))
        except self.module.NotSupportedError, e:
            raise NotSupportedError(ErrorMessage(e))
        except self.module.DatabaseError, e:
            raise DatabaseError(ErrorMessage(e))
        except self.module.InterfaceError, e:
            raise InterfaceError(ErrorMessage(e))
        except self.module.Warning, e:
            raise Warning(ErrorMessage(e))
        except self.module.Error, e:
            raise Error(ErrorMessage(e))

    def _queryInsertID(self, conn, soInstance, id, names, values):
        table = soInstance.sqlmeta.table
        idName = soInstance.sqlmeta.idName
        c = conn.cursor()
        if id is not None:
            names = [idName] + names
            values = [id] + values
        q = self._insertSQL(table, names, values)
        if self.debug:
            self.printDebug(conn, q, 'QueryIns')
        self._executeRetry(conn, c, q)
        # lastrowid is a DB-API extension from "PEP 0249":
        if id is None:
            id = int(c.lastrowid)
        if self.debugOutput:
            self.printDebug(conn, id, 'QueryIns', 'result')
        return id

    def _insertSQL(self, table, names, values):
        if not names:
            assert not values
            # INSERT INTO table () VALUES () isn't allowed in
            # SQLite (though it is in other databases)
            return ("INSERT INTO %s VALUES (NULL)" % table)
        else:
            return DBAPI._insertSQL(self, table, names, values)

    def _queryAddLimitOffset(self, query, start, end):
        if not start:
            return "%s LIMIT %i" % (query, end)
        if not end:
            return "%s LIMIT 0 OFFSET %i" % (query, start)
        return "%s LIMIT %i OFFSET %i" % (query, end-start, start)

    def createColumn(self, soClass, col):
        return col.sqliteCreateSQL()

    def createReferenceConstraint(self, soClass, col):
        return None

    def createIDColumn(self, soClass):
        return self._createIDColumn(soClass.sqlmeta)

    def _createIDColumn(self, sqlmeta):
        key_type = {int: "INTEGER", str: "TEXT"}[sqlmeta.idType]
        return '%s %s PRIMARY KEY' % (sqlmeta.idName, key_type)

    def joinSQLType(self, join):
        return 'INT NOT NULL'

    def tableExists(self, tableName):
        result = self.queryOne("SELECT tbl_name FROM sqlite_master WHERE type='table' AND tbl_name = '%s'" % tableName)
        # turn it into a boolean:
        return not not result

    def viewExists(self, tableName):
        result = self.queryOne("SELECT tbl_name FROM sqlite_master WHERE type='view' AND tbl_name = '%s'" % tableName)
        # turn it into a boolean:
        return not not result

    def tableHasColumn(self, tableName, columnName):
        colData = self.queryOne("SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'"
                                % tableName)
        if not colData:
            return False
        colData = colData[0].split('(', 1)[1].strip()[:-2]
        while colData.find('(') > -1:
            st = colData.find('(')
            en = colData.find(')')
            if en == -1:
                break
            colData = colData[:st] + colData[en+1:]
        results = []
        fields = set()
        for colDesc in colData.split(','):
            parts = colDesc.strip().split(' ', 2)
            field = parts[0].strip()
            # skip comments
            if field.startswith('--'):
                continue
            # get rid of enclosing quotes
            if field[0] == field[-1] == '"':
                field = field[1:-1]
            fields.add(field)
        return columnName in fields

    def dropColumn(self, tableName, column):
        pass

    def createIndexSQL(self, soClass, index):
        return index.sqliteCreateIndexSQL(soClass)

    def addColumn(self, tableName, column):
        self.query('ALTER TABLE %s ADD COLUMN %s' %
                   (tableName,
                    column.sqliteCreateSQL()))
        self.query('VACUUM %s' % tableName)

    def delColumn(self, sqlmeta, column):
        self.recreateTableWithoutColumn(sqlmeta, column)

    def recreateTableWithoutColumn(self, sqlmeta, column):
        new_name = sqlmeta.table + '_ORIGINAL'
        self.query('ALTER TABLE %s RENAME TO %s' % (sqlmeta.table, new_name))
        cols = [self._createIDColumn(sqlmeta)] \
                     + [self.createColumn(None, col)
                        for col in sqlmeta.columnList if col.name != column]
        cols = ",\n".join(["    %s" % c for c in cols])
        self.query('CREATE TABLE %s (\n%s\n)' % (sqlmeta.table, cols))
        all_columns = ', '.join(['id'] + [col.dbName for col in sqlmeta.columnList])
        self.query('INSERT INTO %s (%s) SELECT %s FROM %s' % (
            sqlmeta.table, all_columns, all_columns, new_name))
        self.query('DROP TABLE %s' % new_name)

    def columnsFromSchema(self, tableName, soClass):
        if self.use_table_info:
            return self._columnsFromSchemaTableInfo(tableName, soClass)
        else:
            return self._columnsFromSchemaParse(tableName, soClass)

    def _columnsFromSchemaTableInfo(self, tableName, soClass):
        colData = self.queryAll("PRAGMA table_info(%s)" % tableName)
        results = []
        for index, field, t, nullAllowed, default, key in colData:
            if field == 'id':
                continue
            colClass, kw = self.guessClass(t)
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['dbName'] = field
            kw['notNone'] = not nullAllowed
            kw['default'] = default
            # @@ skip key...
            # @@ skip extra...
            results.append(colClass(**kw))
        return results

    def _columnsFromSchemaParse(self, tableName, soClass):
        colData = self.queryOne("SELECT sql FROM sqlite_master WHERE type='table' AND name='%s'"
                                % tableName)
        if not colData:
            raise ValueError('The table %s ws not found in the database. Load failed.' % tableName)
        colData = colData[0].split('(', 1)[1].strip()[:-2]
        while colData.find('(') > -1:
            st = colData.find('(')
            en = colData.find(')')
            colData = colData[:st] + colData[en+1:]
        results = []
        for colDesc in colData.split(','):
            parts = colDesc.strip().split(' ', 2)
            field = parts[0].strip()
            # skip comments
            if field.startswith('--'):
                continue
            # get rid of enclosing quotes
            if field[0] == field[-1] == '"':
                field = field[1:-1]
            if field == getattr(soClass.sqlmeta, 'idName', 'id'):
                continue
            colClass, kw = self.guessClass(parts[1].strip())
            if len(parts) == 2:
                index_info = ''
            else:
                index_info = parts[2].strip().upper()
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            import re
            nullble = re.search(r'(\b\S*)\sNULL', index_info)
            default = re.search(r"DEFAULT\s((?:\d[\dA-FX.]*)|(?:'[^']*')|(?:#[^#]*#))", index_info)
            kw['notNone'] = nullble and nullble.group(1) == 'NOT'
            kw['default'] = default and default.group(1)
            # @@ skip key...
            # @@ skip extra...
            results.append(colClass(**kw))
        return results

    def guessClass(self, t):
        t = t.upper()
        if t.find('INT') > 0:
            return col.IntCol, {}
        elif t.find('TEXT') > 0 or t.find('CHAR') > 0 or t.find('CLOB') > 0:
            return col.StringCol, {'length': 2**32-1}
        elif t.find('BLOB') > 0:
            return col.BLOBCol, {"length": 2**32-1}
        elif t.find('REAL') > 0 or t.find('FLOAT') > 0:
            return col.FloatCol, {}
        elif t.find('DECIMAL') > 0:
            return col.DecimalCol, {}
        else:
            return col.Col, {}

    def dropDatabase(self, dbname, ifExists=False):
        if os.path.exists(dbname):
            os.unlink(dbname)

    def createDatabase(self, dbname):
        pass

def stop_pysqlite2_converting_strings(s):
    return s
