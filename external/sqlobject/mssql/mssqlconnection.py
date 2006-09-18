from sqlobject.dbconnection import DBAPI
from sqlobject import col
import re

sqlmodule = None

class MSSQLConnection(DBAPI):

    supportTransactions = True
    dbName = 'mssql'
    schemes = [dbName]

    def __init__(self, db, user, password='', host='localhost',
                 autoCommit=0, **kw):
        global sqlmodule
        if not sqlmodule:
            try:
                import adodbapi as sqlmodule
                self.dbconnection = sqlmodule.connect
                # ADO uses unicode only (AFAIK)
                self.usingUnicodeStrings = True

                # Need to use SQLNCLI provider for SQL Server Express Edition
                if kw.get("ncli"):
                    conn_str = "Provider=SQLNCLI;"
                else:
                    conn_str = "Provider=SQLOLEDB;"

                conn_str += "Data Source=%s;Initial Catalog=%s;"

                # MSDE does not allow SQL server login 
                if kw.get("sspi"):
                    conn_str += "Integrated Security=SSPI;Persist Security Info=False"
                    self.make_conn_str = lambda keys: [conn_str % (keys.host, keys.db)]
                else:
                    conn_str += "User Id=%s;Password=%s"
                    self.make_conn_str = lambda keys: [conn_str % (keys.host, keys.db, keys.user, keys.password)]

                col.popKey(kw, "sspi")
                col.popKey(kw, "ncli")

            except ImportError: # raise the exceptions other than ImportError for adodbapi absence
                import pymssql as sqlmodule
                self.dbconnection = sqlmodule.connect
                sqlmodule.Binary = lambda st: str(st)
                # don't know whether pymssql uses unicode
                self.usingUnicodeStrings = False
                self.make_conn_str = lambda keys:  \
                       ["", keys.user, keys.password, keys.host, keys.db]
        self.autoCommit=int(autoCommit)
        self.host = host
        self.db = db
        self.user = user
        self.password = password
        self.limit_re = re.compile('^\s*(select )(.*)', re.IGNORECASE)
        self.password = password
        self.module = sqlmodule
        DBAPI.__init__(self, **kw)

    def connectionFromURI(cls, uri):
        user, password, host, port, path, args = cls._parseURI(uri)
        path = path.strip('/')
        return cls(user=user, password=password, host=host or 'localhost',
                   db=path, **args)
    connectionFromURI = classmethod(connectionFromURI)

    def insert_id(self, conn):
        """
        insert_id method.
        """
        c = conn.cursor()
        # converting the identity to an int is ugly, but it gets returned
        # as a decimal otherwise :S
        c.execute('SELECT CONVERT(INT, @@IDENTITY)')
        return c.fetchone()[0]

    def makeConnection(self):
        con = self.dbconnection( *self.make_conn_str(self) )
        cur = con.cursor()
        cur.execute('SET ANSI_NULLS ON')
        cur.execute("SELECT CAST('12345.21' AS DECIMAL(10, 2))")
        self.decimalSeparator = str(cur.fetchone()[0])[-3]
        cur.close()
        return con

    HAS_IDENTITY = """
       SELECT col.name, col.status, obj.name
       FROM syscolumns col
       JOIN sysobjects obj
       ON obj.id = col.id
       WHERE obj.name = '%s'
       and col.autoval is not null

    """
    def _hasIdentity(self, conn, table):
        query = self.HAS_IDENTITY % table
        c = conn.cursor()
        c.execute(query)
        r = c.fetchone()
        return r is not None

    def _queryInsertID(self, conn, soInstance, id, names, values):
        """
            Insert the Initial with names and values, using id.
        """
        table = soInstance.sqlmeta.table
        idName = soInstance.sqlmeta.idName
        c = conn.cursor()
        has_identity = self._hasIdentity(conn, table)
        if id is not None:
            names = [idName] + names
            values = [id] + values
        elif has_identity and idName in names:
            try:
                i = names.index( idName )
                if i:
                    del names[i]
                    del values[i]
            except ValueError:
                pass

        if has_identity:
            if id is not None:
                c.execute('SET IDENTITY_INSERT %s ON' % table)
            else:
                c.execute('SET IDENTITY_INSERT %s OFF' % table)

        q = self._insertSQL(table, names, values)
        if self.debug:
            print 'QueryIns: %s' % q
        c.execute(q)
        if has_identity:
            c.execute('SET IDENTITY_INSERT %s OFF' % table)

        if id is None:
            id = self.insert_id(conn)
        if self.debugOutput:
            self.printDebug(conn, id, 'QueryIns', 'result')
        return id

    def _queryAddLimitOffset(self, query, start, end):
        if end and not start:
            limit_str = "SELECT TOP %i" % end

            match = self.limit_re.match(query)
            if match and len(match.groups()) == 2:
                return ' '.join([limit_str, match.group(2)])
        else:
            return query

    def createReferenceConstraint(self, soClass, col):
        return col.mssqlCreateReferenceConstraint()

    def createColumn(self, soClass, col):
        return col.mssqlCreateSQL()

    def createIDColumn(self, soClass):
        key_type = {int: "INT", str: "TEXT"}[soClass.sqlmeta.idType]
        return '%s %s IDENTITY UNIQUE' % (soClass.sqlmeta.idName, key_type)

    def createIndexSQL(self, soClass, index):
        return index.mssqlCreateIndexSQL(soClass)

    def joinSQLType(self, join):
        return 'INT NOT NULL'

    SHOW_TABLES="SELECT name FROM sysobjects WHERE type='U'"
    def tableExists(self, tableName):
        for (table,) in self.queryAll(self.SHOW_TABLES):
            if table.lower() == tableName.lower():
                return True
        return False

    def addColumn(self, tableName, column):
        self.query('ALTER TABLE %s ADD %s' %
                   (tableName,
                    column.mssqlCreateSQL()))

    def delColumn(self, tableName, column):
        self.query('ALTER TABLE %s DROP COLUMN %s' %
                   (tableName,
                    column.dbName))

    # precision and scale is gotten from column table so that we can create 
    # decimal columns if needed
    SHOW_COLUMNS = """
        select
                name,
                length,
                (       select name
                        from systypes
                        where cast(xusertype as int)= cast(sc.xtype as int)
                ) datatype,
                prec,
                scale,
                isnullable,
                cdefault,
                m.text default_text,
                isnull(len(autoval),0) is_identity
        from syscolumns sc
        LEFT OUTER JOIN syscomments m on sc.cdefault = m.id
                AND m.colid = 1
        where
                sc.id in (select id
                        from sysobjects
                where name = '%s')
        order by
                colorder"""

    def columnsFromSchema(self, tableName, soClass):
        colData = self.queryAll(self.SHOW_COLUMNS
                                % tableName)
        results = []
        for field, size, t, precision, scale, nullAllowed, default, defaultText, is_identity in colData:
            # Seems strange to skip the pk column?  What if it's not 'id'?
            if field == 'id':
                continue
            # precision is needed for decimal columns
            colClass, kw = self.guessClass(t, size, precision, scale)
            kw['name'] = soClass.sqlmeta.style.dbColumnToPythonAttr(field)
            kw['notNone'] = not nullAllowed
            if (defaultText):
                # Strip ( and )
                defaultText = defaultText[1:-1]
                if defaultText[0] == "'":
                    defaultText = defaultText[1:-1]
                else:
                    if t == "int"    : defaultText = int(defaultText)
                    if t == "float"  : defaultText = float(defaultText)
                    if t == "numeric": defaultText = float(defaultText)
                    # TODO need to access the "column" to_python method here--but the object doesn't exists yet

            # @@ skip key...
            kw['default'] = defaultText

            results.append(colClass(**kw))
        return results

    def _setAutoCommit(self, conn, auto):
        #raise Exception(repr(auto))
        return
        #conn.auto_commit = auto
        option = "ON"
        if auto == 0:
            option = "OFF"
        c = conn.cursor()
        c.execute("SET AUTOCOMMIT " + option)
        conn.setconnectoption(SQL.AUTOCOMMIT, option)

    # precision and scale is needed for decimal columns
    def guessClass(self, t, size, precision, scale):
        """
            Here we take raw values coming out of syscolumns and map to SQLObject class types.
        """
        if t.startswith('int'):
            return col.IntCol, {}
        elif t.startswith('varchar'):
            if self.usingUnicodeStrings:
                return col.UnicodeCol, {'length': size}
            return col.StringCol, {'length': size}
        elif t.startswith('char'):
            if self.usingUnicodeStrings:
                return col.UnicodeCol, {'length': size,
                                       'varchar': False}
            return col.StringCol, {'length': size,
                                   'varchar': False}
        elif t.startswith('datetime'):
            return col.DateTimeCol, {}
        elif t.startswith('decimal'):
            return col.DecimalCol, {'size': precision, # be careful for awkward naming
                                   'precision': scale}
        else:
            return col.Col, {}
