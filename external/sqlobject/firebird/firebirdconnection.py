import re
import os
from sqlobject.dbconnection import DBAPI
from sqlobject import col
kinterbasdb = None

class FirebirdConnection(DBAPI):

    supportTransactions = False
    dbName = 'firebird'
    schemes = [dbName]

    def __init__(self, host, db, user='sysdba',
                 password='masterkey', autoCommit=1,
                 dialect=None, role=None, charset=None, **kw):
        global kinterbasdb
        if kinterbasdb is None:
            import kinterbasdb
        self.module = kinterbasdb

        self.limit_re = re.compile('^\s*(select )(.*)', re.IGNORECASE)

        self.host = host
        self.db = db
        self.user = user
        self.password = password
        if dialect:
            self.dialect = int(dialect)
        else:
            self.dialect = None
        self.role = role
        self.charset = charset

        DBAPI.__init__(self, **kw)

    def connectionFromURI(cls, uri):
        auth, password, host, port, path, args = cls._parseURI(uri)
        if not password:
            password = 'masterkey'
        if not auth:
            auth='sysdba'
        if os.name == 'nt' and path[0] == '/':
            # strip the leading slash off of db name/alias
            path = path[1:]
        path = path.replace('/', os.sep)
        return cls(host, db=path, user=auth, password=password, **args)
    connectionFromURI = classmethod(connectionFromURI)

    def _runWithConnection(self, meth, *args):
        if not self.autoCommit:
            return DBAPI._runWithConnection(self, meth, args)
        conn = self.getConnection()
        # @@: Horrible auto-commit implementation.  Just horrible!
        try:
            conn.begin()
        except kinterbasdb.ProgrammingError:
            pass
        try:
            val = meth(conn, *args)
            try:
                conn.commit()
            except kinterbasdb.ProgrammingError:
                pass
        finally:
            self.releaseConnection(conn)
        return val

    def _setAutoCommit(self, conn, auto):
        # Only _runWithConnection does "autocommit", so we don't
        # need to worry about that.
        pass

    def makeConnection(self):
        extra = {}
        if self.dialect:
            extra['dialect'] = self.dialect
        return kinterbasdb.connect(
            host=self.host,
            database=self.db,
            user=self.user,
            password=self.password,
            role=self.role,
            charset=self.charset,
            **extra
            )

    def _queryInsertID(self, conn, soInstance, id, names, values):
        """Firebird uses 'generators' to create new ids for a table.
        The users needs to create a generator named GEN_<tablename>
        for each table this method to work."""
        table = soInstance.sqlmeta.table
        idName = soInstance.sqlmeta.idName
        sequenceName = getattr(soInstance, '_idSequence',
                               'GEN_%s' % table)
        c = conn.cursor()
        if id is None:
            c.execute('SELECT gen_id(%s,1) FROM rdb$database'
                                % sequenceName)
            id = c.fetchone()[0]
        names = [idName] + names
        values = [id] + values
        q = self._insertSQL(table, names, values)
        if self.debug:
            self.printDebug(conn, q, 'QueryIns')
        c.execute(q)
        if self.debugOutput:
            self.printDebug(conn, id, 'QueryIns', 'result')
        return id

    def _queryAddLimitOffset(self, query, start, end):
        """Firebird slaps the limit and offset (actually 'first' and
        'skip', respectively) statement right after the select."""
        if not start:
            limit_str =  "SELECT FIRST %i" % end
        if not end:
            limit_str = "SELECT SKIP %i" % start
        else:
            limit_str = "SELECT FIRST %i SKIP %i" % (end-start, start)

        match = self.limit_re.match(query)
        if match and len(match.groups()) == 2:
            return ' '.join([limit_str, match.group(2)])
        else:
            return query

    def createTable(self, soClass):
        self.query('CREATE TABLE %s (\n%s\n)' % \
                   (soClass.sqlmeta.table, self.createColumns(soClass)))
        self.query("CREATE GENERATOR GEN_%s" % soClass.sqlmeta.table)

    def createColumn(self, soClass, col):
        return col.firebirdCreateSQL()

    def createIDColumn(self, soClass):
        key_type = {int: "INT", str: "TEXT"}[soClass.sqlmeta.idType]
        return '%s %s NOT NULL PRIMARY KEY' % (soClass.sqlmeta.idName, key_type)

    def createIndexSQL(self, soClass, index):
        return index.firebirdCreateIndexSQL(soClass)

    def joinSQLType(self, join):
        return 'INT NOT NULL'

    def tableExists(self, tableName):
        # there's something in the database by this name...let's
        # assume it's a table.  By default, fb 1.0 stores EVERYTHING
        # it cares about in uppercase.
        result = self.queryOne("SELECT COUNT(rdb$relation_name) FROM rdb$relations WHERE rdb$relation_name = '%s'"
                               % tableName.upper())
        return result[0]

    def addColumn(self, tableName, column):
        self.query('ALTER TABLE %s ADD %s' %
                   (tableName,
                    column.firebirdCreateSQL()))

    def dropTable(self, tableName, cascade=False):
        self.query("DROP TABLE %s" % tableName)
        self.query("DROP GENERATOR GEN_%s" % tableName)

    def delColumn(self, tableName, column):
        self.query('ALTER TABLE %s DROP %s' %
                   (tableName,
                    column.dbName))

    def columnsFromSchema(self, tableName, soClass):
        """
        Look at the given table and create Col instances (or
        subclasses of Col) for the fields it finds in that table.
        """

        fieldqry = """\
        SELECT RDB$RELATION_FIELDS.RDB$FIELD_NAME as field,
               RDB$TYPES.RDB$TYPE_NAME as t,
               RDB$FIELDS.RDB$FIELD_LENGTH as flength,
               RDB$FIELDS.RDB$FIELD_SCALE as fscale,
               RDB$RELATION_FIELDS.RDB$NULL_FLAG as nullAllowed,
               RDB$RELATION_FIELDS.RDB$DEFAULT_VALUE as thedefault,
               RDB$FIELDS.RDB$FIELD_SUB_TYPE as blobtype
        FROM RDB$RELATION_FIELDS
        INNER JOIN RDB$FIELDS ON
            (RDB$RELATION_FIELDS.RDB$FIELD_SOURCE = RDB$FIELDS.RDB$FIELD_NAME)
        INNER JOIN RDB$TYPES ON (RDB$FIELDS.RDB$FIELD_TYPE =
                                 RDB$TYPES.RDB$TYPE)
        WHERE
            (RDB$RELATION_FIELDS.RDB$RELATION_NAME = '%s')
            AND (RDB$TYPES.RDB$FIELD_NAME = 'RDB$FIELD_TYPE')"""

        colData = self.queryAll(fieldqry % tableName.upper())
        results = []
        for field, t, flength, fscale, nullAllowed, thedefault, blobType in colData:
            if field == 'id':
                continue
            colClass, kw = self.guessClass(t, flength, fscale)
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['notNone'] = not nullAllowed
            kw['default'] = thedefault
            results.append(colClass(**kw))
        return results

    _intTypes=['INT64', 'SHORT','LONG']
    _dateTypes=['DATE','TIME','TIMESTAMP']

    def guessClass(self, t, flength, fscale=None):
        """
        An internal method that tries to figure out what Col subclass
        is appropriate given whatever introspective information is
        available -- both very database-specific.
        """

        if t in self._intTypes:
            return col.IntCol, {}
        elif t == 'VARYING':
            return col.StringCol, {'length': flength}
        elif t == 'TEXT':
            return col.StringCol, {'length': flength,
                                   'varchar': False}
        elif t in self._dateTypes:
            return col.DateTimeCol, {}
        else:
            return col.Col, {}
