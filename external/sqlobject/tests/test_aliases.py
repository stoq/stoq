from sqlobject import *
from sqlobject.sqlbuilder import *
from sqlobject.tests.dbtest import *

########################################
## Table aliases and self-joins
########################################

class JoinAlias(SQLObject):
    name = StringCol()
    parent = StringCol()

def test_1syntax():
    setupClass(JoinAlias)
    alias = Alias(JoinAlias)
    select = JoinAlias.select(JoinAlias.q.parent == alias.q.name)
    assert str(select) == \
        "SELECT join_alias.id, join_alias.name, join_alias.parent FROM join_alias AS join_alias_alias1, join_alias WHERE (join_alias.parent = join_alias_alias1.name)"

def test_2perform_join():
    setupClass(JoinAlias)
    JoinAlias(name="grandparent", parent=None)
    JoinAlias(name="parent", parent="grandparent")
    JoinAlias(name="child", parent="parent")
    alias = Alias(JoinAlias)
    select = JoinAlias.select(JoinAlias.q.parent == alias.q.name)
    assert select.count() == 2
