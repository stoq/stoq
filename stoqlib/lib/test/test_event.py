import unittest

from stoqlib.lib.event import Event


class ReturnStatus:
    pass


class TestObject(object):
    def callback(self):
        pass


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

    def test_weak_ref(self):
        class MyEvent(Event):
            returnclass = int

        # lambda will die right after this since there's no other reference
        # to it other than the weakref on event's callbacks
        MyEvent.connect(lambda: 666)
        retval = MyEvent.emit()
        self.assertEqual(retval, None)
