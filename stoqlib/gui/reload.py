# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

"""
gui/reload.py:

   Reload routines
"""



import os, sys, types, time, linecache

#
# Reloader functions
#

def reload_world():
    "reloads all modules, using rebuild for updating module instances"
    global lastRebuild
    print "Reloading changed modules...\n",
    sys.stdout.flush()
    for name, mod in sys.modules.items():
        if mod is None: continue
        if not hasattr(mod, "__file__"): continue # builtins
        if not module_mtime(mod) > lastRebuild: continue
        print "- %s [%s]" % (name, mod.__file__)
        rebuild(mod)
    lastRebuild = time.time()
    print "done"

def module_mtime(module):
    "returns the last modified date for a given module's source file"
    if module.__file__.endswith("pyc"):
        # use [:-1] to stat the actual .py file, not the precompiled version
        return os.stat(module.__file__[:-1])[8]
    return os.stat(module.__file__)[8]

#
# This section from twisted.python.reflect
#

def namedModule(name):
    """Return a module given its name."""
    topLevel = __import__(name)
    packages = name.split(".")[1:]
    m = topLevel
    for p in packages:
        m = getattr(m, p)
    return m

#
# This section from twisted.python.rebuild
#

lastRebuild = time.time()

_modDictIDMap = {}

def latestFunction(oldFunc):
    """Get the latest version of a function.
    """
    # This may be CPython specific, since I believe jython instantiates a new
    # module upon reload.
    dictID = id(oldFunc.func_globals)
    module = _modDictIDMap.get(dictID)
    if module is None:
        return oldFunc
    return getattr(module, oldFunc.__name__)


if sys.version_info >= (2, 2, 0):
    # We have 'object'
    def latestClass(oldClass):
        """Get the latest version of a class.
        """
        module = namedModule(oldClass.__module__)
        newClass = getattr(module, oldClass.__name__)
        newBases = []
        for base in newClass.__bases__:
            newBases.append(latestClass(base))
        
        try:
            # This makes old-style stuff work
            newClass.__bases__ = tuple(newBases)
            return newClass
        except TypeError:
            ctor = getattr(newClass, '__metaclass__', type)
            return ctor(newClass.__name__, tuple(newBases), dict(newClass.__dict__))
else:
    object = 0

    def latestClass(oldClass):
        """Get the latest version of a class.
        """
        module = __import__(oldClass.__module__, {}, {}, 'nothing')
        newClass = getattr(module, oldClass.__name__)
        newBases = []
        for base in newClass.__bases__:
            newBases.append(latestClass(base))
        newClass.__bases__ = tuple(newBases)
        return newClass


def updateInstance(inst):
    """Updates an instance to be current
    """
    inst.__class__ = latestClass(inst.__class__)

def __getattr__(inst, name):
    """A getattr method to cause a class to be refreshed.
    """
    if name == '__del__':
        raise AttributeError("Without this, Python segfaults.")
    updateInstance(inst)
    result = getattr(inst, name)
    return result

def rebuild(module):
    """Reload a module and do as much as possible to replace its references.
    """

    d = module.__dict__
    _modDictIDMap[id(d)] = module
    newclasses = {}
    classes = {}
    functions = {}
    values = {}
    for k, v in d.items():
        if type(v) == types.ClassType:
            # Failure condition -- instances of classes with buggy
            # __hash__/__cmp__ methods referenced at the module level...
            if v.__module__ == module.__name__:
                classes[v] = 1
        elif type(v) == types.FunctionType:
            if v.func_globals is module.__dict__:
                functions[v] = 1
        elif object and isinstance(v, type):
            if v.__module__ == module.__name__:
                newclasses[v] = 1

    values.update(classes)
    values.update(functions)
    fromOldModule = values.has_key
    newclasses = newclasses.keys()
    classes = classes.keys()
    functions = functions.keys()

    # Boom.
    reload(module)
    # Make sure that my traceback printing will at least be recent...
    linecache.clearcache()

    for clazz in classes:
        if getattr(module, clazz.__name__) is clazz:
            pass
        else:
            clazz.__bases__ = ()
            clazz.__dict__.clear()
            clazz.__getattr__ = __getattr__
            clazz.__module__ = module.__name__
    if newclasses:
        import gc
        if (2, 2, 0) <= sys.version_info[:3] < (2, 2, 2):
            hasBrokenRebuild = 1
            gc_objects = gc.get_objects()
        else:
            hasBrokenRebuild = 0
    for nclass in newclasses:
        ga = getattr(module, nclass.__name__)
        if ga is nclass:
            pass
        else:
            if hasBrokenRebuild:
                for r in gc_objects:
                    if not getattr(r, '__class__', None) is nclass:
                        continue
                    r.__class__ = ga
            else:
                for r in gc.get_referrers(nclass):
                    if getattr(r, '__class__', None) is nclass:
                        r.__class__ = ga
    modcount = 0
    for mk, mod in sys.modules.items():
        modcount = modcount + 1
        if mod == module or mod is None:
            continue

        if not hasattr(mod, '__file__'):
            # It's a builtin module; nothing to replace here.
            continue

        for k, v in mod.__dict__.items():
            try:
                hash(v)
            except TypeError:
                continue
            if fromOldModule(v):
                if type(v) == types.ClassType:
                    nv = latestClass(v)
                else:
                    nv = latestFunction(v)
                setattr(mod, k, nv)
            else:
                # Replace bases of non-module classes just to be sure.
                if type(v) == types.ClassType:
                    for base in v.__bases__:
                        if fromOldModule(base):
                            latestClass(v)
    return module

