from dbtest import *
from test_basic import TestSO1
import threading

def test_sqlite_threaded():
    setupClass(TestSO1)
    t = threading.Thread(target=do_select)
    t.start()
    t.join()
    # This should reuse the same connection as the connection
    # made above (at least will with most database drivers, but
    # this will cause an error in SQLite):
    do_select()
    
def do_select():
    list(TestSO1.select())
    print "T", threading.currentThread().getName()
