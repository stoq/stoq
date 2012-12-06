import unittest

from stoqlib.lib.event import Event


class ReturnStatus:
    pass


class EventTest(unittest.TestCase):

    def _stub_return_wrong_value(self):
        return 1

    def _stub_return_corret_value(self):
        return ReturnStatus()

    def testReturnValueNoConnection(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        retval = MyEvent.emit()
        self.assertEquals(None, retval)

    def testWrongReturnValue(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_wrong_value)
        self.assertRaises(TypeError, MyEvent.emit)

    def testCorrectReturnValue(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_corret_value)
        # Shouln't raise
        retval = MyEvent.emit()
        self.assertTrue(isinstance(retval, ReturnStatus))

    def testConnectTwice(self):
        class MyEvent(Event):
            returnclass = ReturnStatus

        MyEvent.connect(self._stub_return_corret_value)
        self.assertRaises(AssertionError,
                          MyEvent.connect, self._stub_return_corret_value)
        MyEvent.disconnect(self._stub_return_corret_value)
        MyEvent.connect(self._stub_return_corret_value)

    def testDisconnect(self):
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

    def testWeakRef(self):
        class MyEvent(Event):
            returnclass = int

        # lambda will die right after this since there's no other reference
        # to it other than the weakref on event's callbacks
        MyEvent.connect(lambda: 666)
        retval = MyEvent.emit()
        self.assertEqual(retval, None)
