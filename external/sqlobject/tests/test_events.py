from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject import events
import sys

class EventTester(SQLObject):
    name = StringCol()

def make_watcher():
    log = []
    def watch(*args):
        log.append(args)
    watch.log = log
    return watch

def make_listen(signal, cls=None):
    if cls is None:
        cls = EventTester
    watcher = make_watcher()
    events.listen(watcher, cls, signal)
    return watcher

def test_create():
    watcher = make_listen(events.ClassCreateSignal)
    class EventTesterSub1(EventTester):
        pass
    class EventTesterSub2(EventTesterSub1):
        pass
    assert len(watcher.log) == 2
    assert len(watcher.log[0]) == 5
    assert watcher.log[0][0] == 'EventTesterSub1'
    assert watcher.log[0][1] == (EventTester,)
    assert isinstance(watcher.log[0][2], dict)
    assert isinstance(watcher.log[0][3], list)

def test_row_create():
    setupClass(EventTester)
    watcher = make_listen(events.RowCreateSignal)
    EventTester(name='foo')
    EventTester(name='bar')
    assert len(watcher.log) == 2
    assert watcher.log[0] == ({'name': 'foo'}, [])

def test_row_destrow():
    setupClass(EventTester)
    watcher = make_listen(events.RowDestroySignal)
    f = EventTester(name='foo')
    assert not watcher.log
    f.destroySelf()
    assert watcher.log == [(f,)]

def test_row_update():
    setupClass(EventTester)
    watcher = make_listen(events.RowUpdateSignal)
    f = EventTester(name='bar')
    assert not watcher.log
    f.name = 'bar2'
    f.set(name='bar3')
    assert watcher.log == [
        (f, {'name': 'bar2'}),
        (f, {'name': 'bar3'})]

def test_add_column():
    setupClass(EventTester)
    watcher = make_listen(events.AddColumnSignal)
    events.summarize_events_by_sender()
    class NewEventTester(EventTester):
        name2 = StringCol()
    expect = (
        NewEventTester, None,
        'name2', NewEventTester.sqlmeta.columnDefinitions['name2'],
        False, [])
    print zip(watcher.log[1], expect)
    assert watcher.log[1] == expect
