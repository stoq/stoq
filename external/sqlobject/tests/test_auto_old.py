from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject import classregistry
try:
    from datetime import datetime
    now = datetime.now
except ImportError:
    from mx.DateTime import now

deprecated_module()

########################################
## Dynamic column tests
########################################

class OldPerson(SQLObject):

    class sqlmeta:
        defaultOrder = 'name'
    _columns = [StringCol('name', length=100, dbName='name_col')]

class OldPhone(SQLObject):

    class sqlmeta:
        defaultOrder = 'phone'
    _columns = [StringCol('phone', length=12)]

class TestPeople:

    def setup_method(self, meth):
        setupClass(OldPerson, force=True)
        setupClass(OldPhone, force=True)
        for n in ['jane', 'tim', 'bob', 'jake']:
            OldPerson(name=n)
        for p in ['555-555-5555', '555-394-2930',
                  '444-382-4854']:
            OldPhone(phone=p)

    def test_defaultOrder(self):
        assert (list(OldPerson.select('all')) ==
                list(OldPerson.select('all', orderBy=OldPerson.sqlmeta.defaultOrder)))

    def test_dynamicColumn(self):
        nickname = StringCol('nickname', length=10)
        OldPerson.addColumn(nickname, changeSchema=True)
        n = OldPerson(name='robert', nickname='bob')
        assert ([p.name for p in OldPerson.select('all')]
                == ['bob', 'jake', 'jane', 'robert', 'tim'])
        OldPerson.delColumn(nickname, changeSchema=True)

    def test_dynamicJoin(self):
        col = KeyCol('oldPersonID', foreignKey='OldPerson')
        OldPhone.addColumn(col, changeSchema=True)
        join = MultipleJoin('OldPhone')
        OldPerson.addJoin(join)
        for phone in OldPhone.select('all'):
            if phone.phone.startswith('555'):
                phone.oldPerson = OldPerson.selectBy(name='tim')[0]
            else:
                phone.oldPerson = OldPerson.selectBy(name='bob')[0]
        l = [p.phone for p in OldPerson.selectBy(name='tim')[0].oldPhones]
        l.sort()
        assert l == ['555-394-2930', '555-555-5555']
        OldPhone.delColumn(col, changeSchema=True)
        OldPerson.delJoin(join)

########################################
## Auto class generation
########################################

class TestAuto:

    mysqlCreate = """
    CREATE TABLE IF NOT EXISTS old_auto_test (
      auto_id INT AUTO_INCREMENT PRIMARY KEY,
      first_name VARCHAR(100),
      last_name VARCHAR(200) NOT NULL,
      age INT DEFAULT NULL,
      created DATETIME NOT NULL,
      happy char(1) DEFAULT 'Y' NOT NULL,
      long_field TEXT,
      wannahavefun TINYINT DEFAULT 0 NOT NULL
    )
    """

    postgresCreate = """
    CREATE TABLE old_auto_test (
      auto_id SERIAL PRIMARY KEY,
      first_name VARCHAR(100),
      last_name VARCHAR(200) NOT NULL,
      age INT DEFAULT 0,
      created VARCHAR(40) NOT NULL,
      happy char(1) DEFAULT 'Y' NOT NULL,
      long_field TEXT,
      wannahavefun BOOL DEFAULT FALSE NOT NULL
    )
    """

    sybaseCreate = """
    CREATE TABLE old_auto_test (
      auto_id integer,
      first_name VARCHAR(100),
      last_name VARCHAR(200) NOT NULL,
      age INT DEFAULT 0,
      created VARCHAR(40) NOT NULL,
      happy char(1) DEFAULT 'Y' NOT NULL,
      long_field TEXT
    )
    """

    mssqlCreate = """
    CREATE TABLE old_auto_test (
      auto_id int IDENTITY(1,1) primary key,
      first_name VARCHAR(100),
      last_name VARCHAR(200) NOT NULL,
      age INT DEFAULT 0,
      created VARCHAR(40) NOT NULL,
      happy char(1) DEFAULT 'Y' NOT NULL,
      long_field TEXT,
      wannahavefun BIT default(0) NOT NULL
    )
    """

    mysqlDrop = """
    DROP TABLE IF EXISTS old_auto_test
    """

    postgresDrop = """
    DROP TABLE old_auto_test
    """

    sybaseDrop = """
    DROP TABLE old_auto_test
    """

    mssqlDrop = """
    DROP TABLE old_auto_test
    """
    def setup_method(self, meth):
        conn = getConnection()
        dbName = conn.dbName
        creator = getattr(self, dbName + 'Create', None)
        if creator:
            conn.query(creator)

    def teardown_method(self, meth):
        conn = getConnection()
        dbName = conn.dbName
        dropper = getattr(self, dbName + 'Drop', None)
        if dropper:
            conn.query(dropper)

    def test_classCreate(self):
        if not supports('fromDatabase'):
            return
        class OldAutoTest(SQLObject):
            _connection = getConnection()
            class sqlmeta(sqlmeta):
                idName = 'auto_id'
                fromDatabase = True
        john = OldAutoTest(firstName='john',
                           lastName='doe',
                           age=10,
                           created=now(),
                           wannahavefun=False,
                           longField='x'*1000)
        jane = OldAutoTest(firstName='jane',
                           lastName='doe',
                           happy='N',
                           created=now(),
                           wannahavefun=True,
                           longField='x'*1000)
        assert not john.wannahavefun
        assert jane.wannahavefun
        assert john.longField == 'x'*1000
        assert jane.longField == 'x'*1000
        del classregistry.registry(
            OldAutoTest.sqlmeta.registry).classes['OldAutoTest']

teardown_module()
