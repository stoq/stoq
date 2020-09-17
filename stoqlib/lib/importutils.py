import importlib


def import_from_string(path):
    try:
        return importlib.import_module(path)
    except ImportError:
        *module_name, obj_name = path.split('.')
        module_name = '.'.join(module_name)
        module = importlib.import_module(module_name)

    try:
        return getattr(module, obj_name)
    except AttributeError:
        raise ImportError('Failed to import {!r}'.format(path))
