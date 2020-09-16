import importlib


def import_from_string(path):
    *module_name, obj_name = path.split('.')
    module = importlib.import_module('.'.join(module_name))
    try:
        return getattr(module, obj_name)
    except AttributeError:
        raise ImportError('Failed to import {!r}'.format(path))
