# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# © 2011 Christopher Arndt, MIT License
# http://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
#

import time


class cached_property(object):
    '''Decorator for read-only properties evaluated only once within TTL period.

    It can be used to created a cached property like this::

        import random

        # the class containing the property must be a new-style class
        class MyClass(object):
            # create property whose value is cached for ten minutes
            @cached_property(ttl=600)
            def randint(self):
                # will only be evaluated every 10 min. at maximum.
                return random.randint(0, 100)

    The value is cached  in the '_cache' attribute of the object instance that
    has the property getter method wrapped by this decorator. The '_cache'
    attribute value is a dictionary which has a key for every property of the
    object which is wrapped by this decorator. Each entry in the cache is
    created only when the property is accessed for the first time and is a
    two-element tuple with the last computed property value and the last time
    it was updated in seconds since the epoch.

    The default time-to-live (TTL) is 300 seconds (5 minutes). Set the TTL to
    zero for the cached value to never expire.

    To expire a cached property value manually just do::

        del instance._cache[<property name>]

    '''
    def __init__(self, ttl=300):
        self.ttl = ttl

    def __call__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        return self

    def __get__(self, inst, owner):
        now = time.time()
        try:
            value, last_update = inst._cache[self.__name__]
            if self.ttl > 0 and now - last_update > self.ttl:
                raise AttributeError
        except (KeyError, AttributeError):
            value = self.fget(inst)
            try:
                cache = inst._cache
            except AttributeError:
                cache = inst._cache = {}
            cache[self.__name__] = (value, now)
        return value


class cached_function(object):
    """Like cached_property but for functions"""
    def __init__(self, ttl=300):
        self._cache = {}
        self.ttl = ttl

    def __call__(self, func):
        def wraps(*args, **kwargs):
            now = time.time()
            try:
                value, last_update = self._cache[args]
                if self.ttl > 0 and now - last_update > self.ttl:
                    raise AttributeError
                return value
            except (KeyError, AttributeError):
                value = func(*args, **kwargs)
                self._cache[args] = (value, now)
                return value
        return wraps


class public:
    """
    A decorator that is used to mark an API public.

    It can be used on classes::

      @public(since="1.0")
      class SomeClass:
          pass

    Or a function/method::

        @public(since="1.0")
        def foo(self, arg):
            pass

    There's an optional argument called *since* which takes a string
    and specifies the version in which this api was added.
    """
    def __init__(self, since=None):
        self.since = since

    def __call__(self, func):
        return func
