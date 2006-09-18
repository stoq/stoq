from sqlobject import *
from sqlobject.tests.dbtest import *

########################################
## Unicode columns
########################################

class Unicode1(SQLObject):
    count = IntCol(alternateID=True)
    col1 = UnicodeCol()
    col2 = UnicodeCol(dbEncoding='latin-1')

try:
    enumerate
except NameError: # Python 2.2
    def enumerate(lst):
        return [(i, lst[i]) for i in range(len(lst))]

def test_create():
    setupClass(Unicode1)
    data = [u'\u00f0', u'test', 'ascii test']

    items = []
    for i, n in enumerate(data):
        items.append(Unicode1(count=i, col1=n, col2=n))
    for n, item in zip(data, items):
        item.col1 = item.col2 = n
    for n, item in zip(data, items):
        assert item.col1 == item.col2
        assert item.col1 == n
    conn = Unicode1._connection
    rows = conn.queryAll("""
    SELECT count, col1, col2
    FROM unicode1
    ORDER BY count
    """)
    for count, col1, col2 in rows:
        assert data[count].encode('utf-8') == col1
        assert data[count].encode('latin1') == col2
