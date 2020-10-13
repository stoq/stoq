import functools
import queue
import threading

from stoqlib.lib.decorators import public


@public(since='6.0.0')
def threaded(original):
    """Threaded decorator

    This will make the decorated function run in a separate thread, and will
    keep the gui responsive by running pending main iterations.

    Note that the result will be syncronous.
    """

    @functools.wraps(original)
    def _run_thread_task(*args, **kwargs):
        from gi.repository import Gtk
        q = queue.Queue()

        # Wrap the actual function inside a try/except so that we can return the
        # exception to the main thread, for it to be reraised
        def f():
            try:
                retval = original(*args, **kwargs)
            except Exception as e:
                return e
            return retval

        # This is the new thread.
        t = threading.Thread(target=lambda q=q: q.put(f()))
        t.daemon = True
        t.start()

        # We we'll wait for the new thread to finish here, while keeping the
        # interface responsive (a nice progress dialog should be displayed)
        while t.is_alive():
            if Gtk.events_pending():
                Gtk.main_iteration_do(False)

        try:
            retval = q.get_nowait()
        except queue.Empty:  # pragma no cover (how do I test this?)
            return None

        if isinstance(retval, Exception):
            # reraise the exception just like if it happened in this thread.
            # This will help catching them by callsites so they can warn
            # the user
            raise retval
        else:
            return retval
    return _run_thread_task
