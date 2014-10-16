import unittest

from stoqlib.lib.event import Event, _WeakRef


class ReturnStatus:
    pass


class TestEvent(Event):
    pass


class TestObject(object):
    def callback(self):
        pass

    @TestEvent.connect
    @classmethod
    def classmethod_callback(cls, list_):
        # We use this to make sure this was called
        list_.append(True)


class EventTest(unittest.TestCase):

    def _stub_return_wrong_value(self):
        return 1

    def _stub_return_corret_value(self):
        return ReturnStatus()

    def test_return_value_no_connection(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        retval = MyEvent.emit()
        self.assertEquals(None, retval)

    def test_wrong_return_value(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_wrong_value)
        self.assertRaises(TypeError, MyEvent.emit)

    def test_correct_return_value(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_corret_value)
        # Shouln't raise
        retval = MyEvent.emit()
        self.assertTrue(isinstance(retval, ReturnStatus))

    def test_connect_twice(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        obj1, obj2 = TestObject(), TestObject()

        # Should fail trying to connect the same callback
        MyEvent.connect(obj1.callback)
        self.assertRaises(AssertionError,
                          MyEvent.connect, obj1.callback)

        # But should let 2 different objects from same type
        MyEvent.connect(obj2.callback)

        # Then Ok after disconnecting
        MyEvent.disconnect(obj1.callback)
        MyEvent.connect(obj1.callback)

    def test_disconnect(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_corret_value)
        retval = MyEvent.emit()
        self.assertTrue(isinstance(retval, ReturnStatus))
        MyEvent.disconnect(self._stub_return_corret_value)
        retval = MyEvent.emit()
        self.assertEqual(retval, None)

        # Trying to disconnect something not connected
        self.assertRaises(ValueError,
                          MyEvent.disconnect, self._stub_return_wrong_value)
        self.assertRaises(ValueError,
                          MyEvent.disconnect, lambda: 666)

    def test_classmethod_callback(self):
        list_ = []
        TestEvent.emit(list_)
        # The callback appends True to the list. This way we are sure it
        # was called and just once
        self.assertEqual(len(list_), 1)
        self.assertEqual(list_[0], True)

    def test_connect_not_callable(self):
        class MyEvent(Event):
            pass

        with self.assertRaisesRegexp(
                TypeError,
                "callback <object object at 0x[0-9a-f]+> must be callable"):
            MyEvent.connect(object())

    def test_weak_ref(self):
        class MyEvent(Event):
            returnclass = int

        # lambda will die right after this since there's no other reference
        # to it other than the weakref on event's callbacks
        MyEvent.connect(lambda: 666)
        retval = MyEvent.emit()
        self.assertEqual(retval, None)

    def test_weakref_comparison(self):
        def xxx():
            pass

        def yyy():
            pass

        zzz = lambda: None

        self.assertEqual(_WeakRef(xxx), _WeakRef(xxx))
        self.assertNotEqual(_WeakRef(xxx), _WeakRef(yyy))
        self.assertNotEqual(_WeakRef(xxx), zzz)
