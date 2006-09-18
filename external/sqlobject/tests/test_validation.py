from sqlobject import *
from sqlobject.tests.dbtest import *
from formencode import validators

########################################
## Validation/conversion
########################################

class SOValidation(SQLObject):

    name = StringCol(validator=validators.PlainText(), default='x', dbName='name_col')
    name2 = StringCol(validator=validators.ConfirmType(type=str), default='y')
    name3 = IntCol(validator=validators.Wrapper(fromPython=int), default=100)
    name4 = FloatCol(default=2.718)

class TestValidation:

    def setup_method(self, meth):
        setupClass(SOValidation)

    def test_validate(self):
        t = SOValidation(name='hey')
        raises(validators.Invalid, setattr, t,
               'name', '!!!')
        t.name = 'you'

    def test_confirmType(self):
        t = SOValidation(name2='hey')
        raises(validators.Invalid, setattr, t,
               'name2', 1)
        raises(validators.Invalid, setattr, t,
               'name3', '1')
        raises(validators.Invalid, setattr, t,
               'name4', '1')
        t.name2 = 'you'

    def test_wrapType(self):
        t = SOValidation(name3=1)
        raises(validators.Invalid, setattr, t,
               'name3', 'x')
        t.name3 = 1L
        assert t.name3 == 1
        t.name3 = 0
        assert t.name3 == 0
