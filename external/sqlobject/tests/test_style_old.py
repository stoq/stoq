from sqlobject import *
from sqlobject.tests.dbtest import *
from sqlobject import styles

deprecated_module()

class AnotherStyle(styles.MixedCaseUnderscoreStyle):
    def pythonAttrToDBColumn(self, attr):
        if attr.lower().endswith('id'):
            return 'id'+styles.MixedCaseUnderscoreStyle.pythonAttrToDBColumn(self, attr[:-2])
        else:
            return styles.MixedCaseUnderscoreStyle.pythonAttrToDBColumn(self, attr)

class OldSOStyleTest1(SQLObject):
    a = StringCol()
    st2 = ForeignKey('OldSOStyleTest2')
    _style = AnotherStyle()

class OldSOStyleTest2(SQLObject):
    b = StringCol()
    _style = AnotherStyle()

def test_style():
    setupClass([OldSOStyleTest2, OldSOStyleTest1])
    st1 = OldSOStyleTest1(a='something', st2=None)
    st2 = OldSOStyleTest2(b='whatever')
    st1.st2 = st2
    assert st1._columnDict['st2ID'].dbName == 'idst2'
    assert st1.st2 == st2

teardown_module()
