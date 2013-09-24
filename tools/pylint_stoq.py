import re
import os

from kiwi.python import namedAny
from logilab.astng import MANAGER, From
from logilab.astng.builder import ASTNGBuilder
from logilab.astng.raw_building import build_function
from storm.info import get_cls_info
from storm.references import Reference

from stoqlib.database.orm import ORMObject
from stoqlib.lib.parameters import sysparam
import stoqlib.domain
import stoqlib.domain.payment


class ORMTypeInfo(object):
    def __init__(self, orm_type):
        self.orm_type = orm_type

    def get_column_names(self):
        info = get_cls_info(self.orm_type)
        for name, attr in info.attributes.items():
            yield name

    def get_foreign_columns(self):
        info = get_cls_info(self.orm_type)
        for name, attr in info.attributes.items():
            if not name.endswith('ID'):
                continue

            name = name[:-2]
            ref = getattr(self.orm_type, name)
            other_class = ref._remote_key.split('.')[0]
            yield name, other_class

    def get_single_joins(self):

        for name, v in self.orm_type.__dict__.items():
            if not isinstance(v, Reference):
                continue
            other_class = v._remote_key.split('.')[0]
            yield name, other_class


class DomainTypeInfo(object):
    def __init__(self):
        self.orm_classes = {}
        self._scan_modules()
        self.done = set()

    def _scan_modules(self):
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

        orm_ti = dt.orm_classes.get(orm_name)
        if orm_ti is not None:
            for name in sorted(orm_ti.get_column_names()):
                t += '    %s = None\n' % (name, )

            for name, class_name in sorted(orm_ti.get_foreign_columns()):
                self.add_ormobject(dt.orm_classes[class_name].orm_type,
                                   class_name)
                t += '    %s = None\n' % (class_name, )
                t += '    %s = %s()\n' % (name, class_name)

            for name, class_name in sorted(orm_ti.get_single_joins()):
                self.add_ormobject(
                    dt.orm_classes[class_name].orm_type,
                    class_name)
                t += '    %s = %s()\n' % (name, class_name)

        t += '\n'
        nodes = self.builder.string_build(t)
        for key, value in nodes[orm_name].items():
            class_node.locals[key] = [value]

    def add_interfaces(self, module):
        f = namedAny(module.name).__file__.replace('.pyc', '.py')
        data = open(f).read()
        data = re.sub(r'(def \S+)\(\)', r'\1(self)', data)
        data = re.sub(r'(def \S+)\(', r'\1(self, ', data)
        data = data.replace('self, self', 'self')
        nodes = self.builder.string_build(data)
        self.module.locals = nodes.locals

    def add_wizard_step(self, module):
        from stoqlib.gui.wizards.purchasewizard import WizardEditorStep
        pymod = namedAny(module.name)
        for attr in dir(pymod):
            value = getattr(pymod, attr)
            if attr in module and isinstance(module[attr], From):
                continue

            if my_issubclass(value, WizardEditorStep):
                self.add_delegate(value, attr)

    def add_delegate(self, delegate, attr):
        from kiwi.environ import environ
        from kiwi.ui.builderloader import BuilderWidgetTree
        import gtk
        if not delegate.gladefile:
            return
        f = environ.find_resource('glade', delegate.gladefile + '.ui')
        tree = BuilderWidgetTree(delegate, f, None)

        t = ''
        t += 'import kiwi\n'
        t += 'class %s(object):\n' % (attr, )
        for widget in sorted(tree.get_widgets()):
            try:
                name = gtk.Buildable.get_name(widget)
            except TypeError:
                continue
            t += '    %s = %s.%s()\n' % (name,
                                         widget.__module__,
                                         widget.__class__.__name__)

        print t
        real_node = self.module[attr]
        self.module.body.remove(real_node)
        print vars(self.module)
        nodes = self.builder.string_build(t)
        for key, value in nodes.items():
            self.module.locals[key] = [value]
            self.module.body.append(value)

        new_node = self.module.locals[attr][0]
        for key, value in real_node.locals.items():
            print key
            new_node[key] = [value]


def stoq_transform(module):
    fake = FakeBuilder(module)
    if module.name == 'hashlib':
        nodes = fake.builder.string_build("""
class _Internal:
    def hexdigest(self):
        return hash('foo')
def md5(enc):
    return _Internal()""")
        module.locals = nodes.locals
    if module.name == 'storm.info':
        # Actually we only need an override for ClassAlias,
        # but I don't know how to just override one attribute,
        # so implement the whole API we need.
        nodes = fake.builder.string_build("""
class ClassInfo(dict):
    columns = []
def ClassAlias(class_, b):
    return class_
def get_cls_info(cls):
    return ClassInfo()
def get_obj_info(obj):
    return {}
""")
        module.locals = nodes.locals

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
    #elif module.name == 'stoqlib.gui.wizards.purchasewizard':
    #    fake.add_wizard_step(module)


def register(linter):
    """called when loaded by pylint --load-plugins, register our tranformation
    function here
    """
    MANAGER.register_transformer(stoq_transform)
