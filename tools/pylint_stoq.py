import re
import os

from logilab.astng import MANAGER, From, AssName
from logilab.astng.builder import ASTNGBuilder

from kiwi.python import namedAny
from stoqlib.database.orm import SOCol, Col, SOForeignKey
from stoqlib.database.orm import SOSingleJoin, SOMultipleJoin
from stoqlib.database.orm import ORMObject, Viewable
from stoqlib.lib.parameters import get_all_details
import stoqlib.domain
import stoqlib.domain.payment


class ORMTypeInfo(object):
    def __init__(self, orm_type):
        self.orm_type = orm_type

    def get_columns(self):
        return self.orm_type.sqlmeta.columns.values()

    def get_foreign_columns(self):
        foreign = []
        for column in self.get_columns():
            if isinstance(column, SOForeignKey):
                foreign.append(column)
        return foreign

    def get_single_joins(self):
        signle = []
        for column in self.orm_type.sqlmeta.joins:
            if isinstance(column, (SOSingleJoin, SOMultipleJoin)):
                signle.append(column)
        return signle


class DomainTypeInfo(object):
    def __init__(self):
        self.orm_classes = {}
        self._scan_modules()
        self.done = set()

    def _scan_modules(self):
        classes = {}
        for package, module in [
            ('stoqlib.domain', stoqlib.domain),
            ('stoqlib.domain.payment',
             stoqlib.domain.payment)]:
            files = os.listdir(os.path.dirname(module.__file__))
            for filename in files:
                if filename == '__init__.py':
                    continue
                if not filename.endswith('.py'):
                    continue
                name = filename[:-3]
                self._scan_module(package, name)

    def _scan_module(self, package, name):
        module_name = '%s.%s' % (package, name)
        module = namedAny(module_name)
        for attr in dir(module):
            value = getattr(module, attr)
            if not my_issubclass(value, ORMObject):
                continue
            self._scan_orm_object(module, value)

    def _scan_orm_object(self, module, orm_type):
        if module.__name__ != orm_type.__module__:
            return
        self.orm_classes[orm_type.__name__] = ORMTypeInfo(orm_type)


def my_issubclass(value, class_):
    try:
        return issubclass(value, class_)
    except TypeError:
        return False


dt = DomainTypeInfo()


class FakeBuilder(object):
    def __init__(self, module):
        self.builder = ASTNGBuilder(MANAGER)
        self.module = module

    def add_ormobject(self, orm_type, orm_name):
        if orm_type in dt.done:
            return
        dt.done.add(orm_type)
        selectOneByArgs = ['connection']
        module_name = orm_type.__module__
        pymodule = namedAny(module_name)
        assert pymodule
        module = MANAGER.astng_from_module(pymodule)
        assert module
        class_node = module[orm_name]

        t = ''
        t += 'class %s:\n' % (orm_name, )

        t += '    q = None\n'
        t += '    _connection = None\n'
        t += '    def get_connection(self): pass\n'
        t += '    def selectOneBy(self, connection=None): pass\n'

        orm_ti = dt.orm_classes.get(orm_name)
        for col in sorted(orm_ti.get_columns()):
            t += '    def _SO_set_%s(self, value): pass\n' % (col.name, )

        for col in sorted(orm_ti.get_columns()):
            t += '    %s = None\n' % (col.name, )

        for col in sorted(orm_ti.get_foreign_columns()):
            self.add_ormobject(
                dt.orm_classes[col.foreignKey].orm_type,
                col.foreignKey)
            t += '    %s = None\n' % (col.name, )
            t += '    %s = %s()\n' % (col.foreignName,
                                      col.foreignKey)

        for join in sorted(orm_ti.get_single_joins()):
            self.add_ormobject(
                dt.orm_classes[join.otherClassName].orm_type,
                join.otherClassName)
            t += '    %s = %s()\n' % (join.joinMethodName,
                                      join.otherClassName)

        t += '\n'
        nodes = self.builder.string_build(t)
        for key, value in nodes[orm_name].items():
            class_node.locals[key] = [value]

    def add_viewable(self, viewable, attr):
        viewable_node = self.module[attr]

        t = ''
        t += 'class FakeViewable:\n'
        t += '    q = None\n'
        t += '    _connection = None\n'
        t += '    def get_connection(self): pass\n'
        nodes = self.builder.string_build(t)
        for key, value in nodes['FakeViewable'].items():
            viewable_node[key] = value

        for name in viewable.columns.keys():
            viewable_node[name] = AssName()
        viewable_node['q'] = AssName()

    def add_parameter_access(self):
        name = 'ParameterAccess'
        t = 'class %s(object):\n' % (name, )
        for detail in get_all_details():
            t += '    def %s(self): pass\n' % (detail.key, )
        nodes = self.builder.string_build(t)
        self.module.locals[name] = nodes.locals[name]

    def add_interfaces(self, module):
        f = namedAny(module.name).__file__.replace('.pyc', '.py')
        data = open(f).read()
        data = re.sub(r'(def \S+)\(\)', r'\1(self)', data)
        data = re.sub(r'(def \S+)\(', r'\1(self, ', data)
        data = data.replace('self, self', 'self')
        nodes = self.builder.string_build(data)
        self.module.locals = nodes.locals


def stoq_transform(module):
    fake = FakeBuilder(module)
    if module.name == 'stoqlib.domain.base':
        pass
    if module.name == 'stoqlib.domain.interfaces':
        fake.add_interfaces(module)
    elif module.name.startswith('stoqlib.domain.'):
        pymod = namedAny(module.name)
        for attr in dir(pymod):
            value = getattr(pymod, attr)
            if attr in module and isinstance(module[attr], From):
                continue

            if my_issubclass(value, ORMObject):
                fake.add_ormobject(value, attr)
            elif my_issubclass(value, Viewable):
                fake.add_viewable(value, attr)
    elif module.name == 'stoqlib.lib.parameters':
        fake.add_parameter_access()
    elif module.name == 'kiwi.log':
        nodes = fake.builder.string_build(
"""class Logger(object):
    def info(self, msg):
        pass
""")
        module.locals = nodes.locals

def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(stoq_transform)
