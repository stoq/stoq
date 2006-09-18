from sqlobject.dbconnection import DBAPI
import re
from sqlobject import col
from sqlobject import sqlbuilder
from sqlobject.converters import registerConverter
psycopg = None
pgdb = None

class PostgresConnection(DBAPI):

    supportTransactions = True
    dbName = 'postgres'
    schemes = [dbName, 'postgresql', 'psycopg']

    def __init__(self, dsn=None, host=None, port=None, db=None,
                 user=None, password=None, usePygresql=False, unicodeCols=False,
                 **kw):
        global psycopg, pgdb
        self.usePygresql = usePygresql
        if usePygresql:
            if pgdb is None:
                import pgdb
            self.module = pgdb
        else:
            if psycopg is None:
                try:
                    import psycopg2 as psycopg
                except ImportError:
                    import psycopg
            self.module = psycopg

            # Register a converter for psycopg Binary type.
            registerConverter(type(psycopg.Binary('')),
                              PsycoBinaryConverter)

        self.user = user
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.dsn_dict = dsn_dict = {}
        if host:
            dsn_dict["host"] = host
        if port:
            if usePygresql:
                dsn_dict["host"] = "%s:%d" % (host, port)
            else:
                dsn_dict["port"] = str(port)
        if db:
            dsn_dict["database"] = db
        if user:
            dsn_dict["user"] = user
        if password:
            dsn_dict["password"] = password
        self.use_dsn = dsn is not None
        if dsn is None:
            if usePygresql:
                dsn = ''
                if host:
                    dsn += host
                dsn += ':'
                if db:
                    dsn += db
                dsn += ':'
                if user:
                    dsn += user
                dsn += ':'
                if password:
                    dsn += password
            else:
                dsn = []
                if db:
                    dsn.append('dbname=%s' % db)
                if user:
                    dsn.append('user=%s' % user)
                if password:
                    dsn.append('password=%s' % password)
                if host:
                    dsn.append('host=%s' % host)
                if port:
                    dsn.append('port=%d' % port)
                dsn = ' '.join(dsn)
        self.dsn = dsn
        self.unicodeCols = unicodeCols
        DBAPI.__init__(self, **kw)

        # Server version cache
        self._server_version = None # Not yet initialized

    def connectionFromURI(cls, uri):
        user, password, host, port, path, args = cls._parseURI(uri)
        path = path.strip('/')
        return cls(host=host, port=port, db=path, user=user, password=password, **args)
    connectionFromURI = classmethod(connectionFromURI)

    def _setAutoCommit(self, conn, auto):
        # psycopg2 does not have an autocommit method.
        if hasattr(conn, 'autocommit'):
            conn.autocommit(auto)

    def makeConnection(self):
        try:
            if self.use_dsn:
                conn = self.module.connect(self.dsn)
            else:
                conn = self.module.connect(**self.dsn_dict)
        except self.module.OperationalError, e:
            raise self.module.OperationalError("%s; used connection string %r" % (e, self.dsn))
        if self.autoCommit:
            # psycopg2 does not have an autocommit method.
            if hasattr(conn, 'autocommit'):
                conn.autocommit(1)
        return conn

    def _queryInsertID(self, conn, soInstance, id, names, values):
        table = soInstance.sqlmeta.table
        idName = soInstance.sqlmeta.idName
        sequenceName = getattr(soInstance, '_idSequence',
                               '%s_%s_seq' % (table, idName))
        c = conn.cursor()
        if id is None:
            c.execute("SELECT NEXTVAL('%s')" % sequenceName)
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
        if not start:
            return "%s LIMIT %i" % (query, end)
        if not end:
            return "%s OFFSET %i" % (query, start)
        return "%s LIMIT %i OFFSET %i" % (query, end-start, start)

    def createColumn(self, soClass, col):
        return col.postgresCreateSQL()

    def createReferenceConstraint(self, soClass, col):
        return col.postgresCreateReferenceConstraint()

    def createIndexSQL(self, soClass, index):
        return index.postgresCreateIndexSQL(soClass)

    def createIDColumn(self, soClass):
        key_type = {int: "SERIAL", str: "TEXT"}[soClass.sqlmeta.idType]
        return '%s %s PRIMARY KEY' % (soClass.sqlmeta.idName, key_type)

    def dropTable(self, tableName, cascade=False):
        if self.server_version[:3] <= "7.2":
            cascade=False
        self.query("DROP TABLE %s %s" % (tableName,
                                         cascade and 'CASCADE' or ''))

    def joinSQLType(self, join):
        return 'INT NOT NULL'

    def tableExists(self, tableName):
        result = self.queryOne("SELECT COUNT(relname) FROM pg_class WHERE relname = %s"
                               % self.sqlrepr(tableName))
        return result[0]

    def addColumn(self, tableName, column):
        self.query('ALTER TABLE %s ADD COLUMN %s' %
                   (tableName,
                    column.postgresCreateSQL()))

    def delColumn(self, tableName, column):
        self.query('ALTER TABLE %s DROP COLUMN %s' %
                   (tableName,
                    column.dbName))

    def columnsFromSchema(self, tableName, soClass):

        keyQuery = """
        SELECT pg_catalog.pg_get_constraintdef(oid) as condef
        FROM pg_catalog.pg_constraint r
        WHERE r.conrelid = %s::regclass AND r.contype = 'f'"""

        colQuery = """
        SELECT a.attname,
        pg_catalog.format_type(a.atttypid, a.atttypmod), a.attnotnull,
        (SELECT substring(d.adsrc for 128) FROM pg_catalog.pg_attrdef d
        WHERE d.adrelid=a.attrelid AND d.adnum = a.attnum)
        FROM pg_catalog.pg_attribute a
        WHERE a.attrelid =%s::regclass
        AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum"""

        primaryKeyQuery = """
        SELECT pg_index.indisprimary,
            pg_catalog.pg_get_indexdef(pg_index.indexrelid)
        FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
            pg_catalog.pg_index AS pg_index
        WHERE c.relname = %s
            AND c.oid = pg_index.indrelid
            AND pg_index.indexrelid = c2.oid
            AND pg_index.indisprimary
        """

        keyData = self.queryAll(keyQuery % self.sqlrepr(tableName))
        keyRE = re.compile(r"\((.+)\) REFERENCES (.+)\(")
        keymap = {}

        for (condef,) in keyData:
            match = keyRE.search(condef)
            if match:
                field, reftable = match.groups()
                keymap[field] = reftable.capitalize()

        primaryData = self.queryAll(primaryKeyQuery % self.sqlrepr(tableName))
        primaryRE = re.compile(r'CREATE .*? USING .* \((.+?)\)')
        primaryKey = None
        for isPrimary, indexDef in primaryData:
            match = primaryRE.search(indexDef)
            assert match, "Unparseable contraint definition: %r" % indexDef
            assert primaryKey is None, "Already found primary key (%r), then found: %r" % (primaryKey, indexDef)
            primaryKey = match.group(1)
        assert primaryKey, "No primary key found in table %r" % tableName
        if primaryKey.startswith('"'):
            assert primaryKey.endswith('"')
            primaryKey = primaryKey[1:-1]

        colData = self.queryAll(colQuery % self.sqlrepr(tableName))
        results = []
        if self.unicodeCols:
            client_encoding = self.queryOne("SHOW client_encoding")[0]
        for field, t, notnull, defaultstr in colData:
            if field == primaryKey:
                continue
            colClass, kw = self.guessClass(t)
            if self.unicodeCols and colClass == col.StringCol:
                colClass = col.UnicodeCol
                kw['dbEncoding'] = client_encoding
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['dbName'] = field
            kw['notNone'] = notnull
            if defaultstr is not None:
                kw['default'] = self.defaultFromSchema(colClass, defaultstr)
            elif not notnull:
                kw['default'] = None
            if keymap.has_key(field):
                kw['foreignKey'] = keymap[field]
            results.append(colClass(**kw))
        return results

    def guessClass(self, t):
        if t.count('int'):
            return col.IntCol, {}
        elif t.count('varying') or t.count('varchar'):
            if '(' in t:
                return col.StringCol, {'length': int(t[t.index('(')+1:-1])}
            else: # varchar without length in Postgres means any length
                return col.StringCol, {}
        elif t.startswith('character('):
            return col.StringCol, {'length': int(t[t.index('(')+1:-1]),
                                   'varchar': False}
        elif t.count('float') or t.count('real') or t.count('double'):
            return col.FloatCol, {}
        elif t == 'text':
            return col.StringCol, {}
        elif t.startswith('timestamp'):
            return col.DateTimeCol, {}
        elif t.startswith('datetime'):
            return col.DateTimeCol, {}
        elif t.startswith('date'):
            return col.DateCol, {}
        elif t.startswith('bool'):
            return col.BoolCol, {}
        elif t.startswith('bytea'):
            return col.BLOBCol, {}
        else:
            return col.Col, {}

    def defaultFromSchema(self, colClass, defaultstr):
        """
        If the default can be converted to a python constant, convert it.
        Otherwise return is as a sqlbuilder constant.
        """
        if colClass == col.BoolCol:
            if defaultstr == 'false':
                return False
            elif defaultstr == 'true':
                return True
        return getattr(sqlbuilder.const, defaultstr)

    def server_version(self):
        if self._server_version is None:
            # The result is something like
            # ' PostgreSQL 7.2.1 on i686-pc-linux-gnu, compiled by GCC 2.95.4'
            server_version = self.queryOne("SELECT version()")[0]
            self._server_version = server_version.split()[1]
        return self._server_version
    server_version = property(server_version)

    def createEmptyDatabase(self):
        # We have to connect to *some* database, so we'll connect to
        # template1, which is a common open database.
        # @@: This doesn't use self.use_dsn or self.dsn_dict
        if self.usePygresql:
            dsn = '%s:template1:%s:%s' % (
                self.host or '', self.user or '', self.password or '')
        else:
            dsn = 'dbname=template1'
            if self.user:
                dsn += ' user=%s' % self.user
            if self.password:
                dsn += ' password=%s' % self.password
            if self.host:
                dsn += ' host=%s' % self.host
        conn = self.module.connect(dsn)
        cur = conn.cursor()
        # We must close the transaction with a commit so that
        # the CREATE DATABASE can work (which can't be in a transaction):
        cur.execute('COMMIT')
        cur.execute('CREATE DATABASE %s' % self.db)
        cur.close()
        conn.close()



# Converter for psycopg Binary type.
def PsycoBinaryConverter(value, db):
    assert db == 'postgres'
    return str(value)
