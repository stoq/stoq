# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# © 2011 Christopher Arndt, MIT License
# http://wiki.python.org/moin/PythonDecoratorLibrary#Cached_Properties
#

import inspect
import time
import functools
import logging
import Queue
import sys
import threading
import traceback

log = logging.getLogger(__name__)


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

            # Use inspect.getcallargs so that we have all positional arguments
            # with their respective names
            args_dict = inspect.getcallargs(func, *args, **kwargs)
            if len(args_dict) == len(args) + len(kwargs):
                # This means all args and kwargs were converted to the named
                # arguments, and we can use it as a key.
                key = tuple(sorted(args_dict.items()))
            else:
                # otherwise, just use them separately
                key = (args, tuple(sorted(kwargs.items())))

            try:
                value, last_update = self._cache[key]
                if self.ttl > 0 and now - last_update > self.ttl:
                    raise AttributeError
                return value
            except (KeyError, AttributeError):
                value = func(*args, **kwargs)
                self._cache[key] = (value, now)
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


@public(since='1.13')
def threaded(original):
    """Threaded decorator

    This will make the decorated function run in a separate thread, and will
    keep the gui responsive by running pending main iterations.

    Note that the result will be syncronous.
    """

    @functools.wraps(original)
    def _run_thread_task(*args, **kwargs):
        import gtk
        q = Queue.Queue()

        # Wrap the actual function inside a try/except so that we can return the
        # exception to the main thread, for it to be reraised
        def f():
            try:
                retval = original(*args, **kwargs)
            except Exception as e:
                log.error(''.join(traceback.format_exception(*sys.exc_info())))
                return e
            return retval

        # This is the new thread.
        t = threading.Thread(target=lambda q=q: q.put(f()))
        t.daemon = True
        t.start()

        # We we'll wait for the new thread to finish here, while keeping the
        # interface responsive (a nice progress dialog should be displayed)
        while t.is_alive():
            if gtk.events_pending():
                gtk.main_iteration(False)

        try:
            retval = q.get_nowait()
        except Queue.Empty:  # pragma no cover (how do I test this?)
            return None

        if isinstance(retval, Exception):
            # reraise the exception just like if it happened in this thread.
            # This will help catching them by callsites so they can warn
            # the user
            raise retval
        else:
            return retval
    return _run_thread_task
