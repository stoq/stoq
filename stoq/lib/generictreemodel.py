# System
import random
import traceback
import collections
import weakref

# GObject
from gi.repository import GObject
from gi.repository import Gtk


def handle_exception(default_return):
    """Returns a function which can act as a decorator for wrapping exceptions and
    returning "default_return" upon an exception being thrown.

    This is used to wrap Gtk.TreeModel "do_" method implementations so we can return
    a proper value from the override upon an exception occurring with client code
    implemented by the "on_" methods.
    """
    def decorator(func):
        def wrapped_func(*args, **kargs):
            try:
                return func(*args, **kargs)
            except:
                traceback.print_exc()
            return default_return
        return wrapped_func
    return decorator


class GenericTreeModel(GObject.GObject, Gtk.TreeModel):
    """A base implementation of a Gtk.TreeModel for python.

    The GenericTreeModel eases implementing the Gtk.TreeModel interface in Python.
    The class can be subclassed to provide a TreeModel implementation which works
    with subclass supplied Python objects instead of iterators.

    All of the on_* methods should be overridden by subclasses to provide the
    underlying implementation a way to access custom model data. For the purposes of
    this API, all custom model data supplied or handed back through the overridable
    API will use the argument names: node, parent, and child in regards to user data
    python objects.

    The create_tree_iter, set_user_data, invalidate_iters, iter_is_valid methods are
    available to help manage Gtk.TreeIter objects and their Python object references.

    GenericTreeModel manages a pool of user data nodes that have been used with iters.
    This pool stores a references to user data nodes as a dictionary value with the
    key being the integer id of the data. This id is what the Gtk.TreeIter objects
    use to reference to data.
    References will be removed from the pool when the model is deleted or explicitly
    by using the optional "node" argument to the "row_deleted" method when notifying
    the model of row deletion.
    """

    #
    # Methods
    #
    def __init__(self):
        """Initialize. Make sure to call this from derived classes if overridden."""
        super(GenericTreeModel, self).__init__()
        self.stamp = 0

        #: Backing data for the leak_references property.
        self._leak_refs = True

        #: Dictionary of (id(user_data): user_data), this will be a WeakValueDictionary
        #: when leak_references is False.
        self._held_refs = dict()

        # Set initial stamp
        self.invalidate_iters()

    def _get_leak_references(self):
        """If True, strong references to user data attached to iters are stored in a dictionary
        pool (default). Otherwise the user data is stored in a WeakValue dictionary."""
        return self._leak_refs

    def _set_leak_references(self, value):
        self._leak_refs = value
        if True: #or value:
            self._held_refs = dict(self._held_refs)
        else:
            self._held_refs = weakref.WeakValueDictionary(self._held_refs)

    leak_references = GObject.Property(default=True, type=bool,
            setter=_set_leak_references,
            getter=_get_leak_references)

    def iter_depth_first(self):
        """Depth-first iteration of the entire TreeModel yielding the python nodes."""
        stack = collections.deque([None])
        while stack:
            it = stack.popleft()
            if it is not None:
                yield self.get_user_data(it)
            children = [self.iter_nth_child(it, i) for i in range(self.iter_n_children(it))]
            stack.extendleft(reversed(children))

    def invalidate_iters(self):
        """
        This method invalidates all TreeIter objects associated with this custom tree model
        and frees their locally pooled references.
        """
        self.stamp = random.randint(-2147483648, 2147483647)
        self._held_refs.clear()

    def iter_is_valid(self, iter):
        """
        :Returns:
            True if the gtk.TreeIter specified by iter is valid for the custom tree model.
        """
        return iter.stamp == self.stamp

    def get_user_data(self, iter):
        """Get the user_data associated with the given TreeIter.

        GenericTreeModel stores arbitrary Python objects mapped to instances of Gtk.TreeIter.
        This method allows to retrieve the Python object held by the given iterator.
        """
        return self._held_refs[iter.user_data]

    def set_user_data(self, iter, user_data):
        """Applies user_data and stamp to the given iter.

        If the models "leak_references" property is set, a reference to the
        user_data is stored with the model to ensure we don't run into bad
        memory problems with the TreeIter.
        """

        user_data_id = id(user_data)
        iter.user_data = user_data_id

        if user_data is None:
            iter.stamp = 0
            if user_data_id in self._held_refs:
                del self._held_refs[user_data_id]
        else:
            iter.stamp = self.stamp
            self._held_refs[user_data_id] = user_data

    def create_tree_iter(self, user_data):
        """Create a Gtk.TreeIter instance with the given user_data specific for this model.

        Use this method to create Gtk.TreeIter instance instead of directly calling
        Gtk.Treeiter(), this will ensure proper reference managment of wrapped used_data.
        """
        iter = Gtk.TreeIter()
        self.set_user_data(iter, user_data)
        return iter

    def _create_tree_iter(self, data):
        """Internal creation of a (bool, TreeIter) pair for returning directly
        back to the view interfacing with this model."""
        if data:
            it = self.create_tree_iter(data)
            return (True, it)
        else:
            return (False, None)

    def row_deleted(self, path, node=None):
        """Notify the model a row has been deleted.

        Use the node parameter to ensure the user_data reference associated
        with the path is properly freed by this model.

        :Parameters:
            path : Gtk.TreePath
                Path to the row that has been deleted.
            node : object
                Python object used as the node returned from "on_get_iter". This is
                optional but ensures the model will not leak references to this object.
        """
        super(GenericTreeModel, self).row_deleted(path)
        node_id = id(node)
        if node is not None and node_id in self._held_refs:
            del self._held_refs[node_id]

    #
    # GtkTreeModel Interface Implementation
    #
    @handle_exception(0)
    def do_get_flags(self):
        """Internal method."""
        return self.on_get_flags()

    @handle_exception(0)
    def do_get_n_columns(self):
        """Internal method."""
        return self.on_get_n_columns()

    @handle_exception((False, None))
    def do_get_column_type(self, index):
        """Internal method."""
        return self.on_get_column_type(index)

    @handle_exception((False, None))
    def do_get_iter(self, path):
        """Internal method."""
        return self._create_tree_iter(self.on_get_iter(path))

    @handle_exception(False)
    def do_iter_next(self, iter):
        """Internal method."""
        if iter is None:
            next_data = self.on_iter_next(None)
        else:
            next_data = self.on_iter_next(self.get_user_data(iter))

        self.set_user_data(iter, next_data)
        return next_data is not None

    @handle_exception(None)
    def do_get_path(self, iter):
        """Internal method."""
        path = self.on_get_path(self.get_user_data(iter))
        if path is None:
            return None
        else:
            return Gtk.TreePath(path)

    @handle_exception(None)
    def do_get_value(self, iter, column):
        """Internal method."""
        return self.on_get_value(self.get_user_data(iter), column)

    @handle_exception((False, None))
    def do_iter_children(self, parent):
        """Internal method."""
        data = self.get_user_data(parent) if parent else None
        return self._create_tree_iter(self.on_iter_children(data))

    @handle_exception(False)
    def do_iter_has_child(self, parent):
        """Internal method."""
        return self.on_iter_has_child(self.get_user_data(parent))

    @handle_exception(0)
    def do_iter_n_children(self, iter):
        """Internal method."""
        if iter is None:
            return self.on_iter_n_children(None)
        return self.on_iter_n_children(self.get_user_data(iter))

    @handle_exception((False, None))
    def do_iter_nth_child(self, parent, n):
        """Internal method."""
        if parent is None:
            data = self.on_iter_nth_child(None, n)
        else:
            data = self.on_iter_nth_child(self.get_user_data(parent), n)
        return self._create_tree_iter(data)

    @handle_exception((False, None))
    def do_iter_parent(self, child):
        """Internal method."""
        return self._create_tree_iter(self.on_iter_parent(self.get_user_data(child)))

    @handle_exception(None)
    def do_ref_node(self, iter):
        pass  # self.on_ref_node(self.get_user_data(iter))

    @handle_exception(None)
    def do_unref_node(self, iter):
        pass  # self.on_unref_node(self.get_user_data(iter))

    #
    # Python Subclass Overridables
    #
    def on_get_flags(self):
        """Overridable.

        :Returns Gtk.TreeModelFlags:
            The flags for this model. See: Gtk.TreeModelFlags
        """
        raise NotImplementedError

    def on_get_n_columns(self):
        """Overridable.

        :Returns:
            The number of columns for this model.
        """
        raise NotImplementedError

    def on_get_column_type(self, index):
        """Overridable.

        :Returns:
            The column type for the given index.
        """
        raise NotImplementedError

    def on_get_iter(self, path):
        """Overridable.

        :Returns:
            The a python object (or node) for the given TreePath.
        """
        raise NotImplementedError

    def on_get_path(self, node):
        """Overridable.

        :Returns:
            A TreePath for the given node.
        """
        raise NotImplementedError

    def on_get_value(self, node, column):
        """Overridable.

        :Parameters:
            node : object
            column : int
                Column index to get the value from.

        :Returns:
            The value of the column for the given node."""
        raise NotImplementedError

    def on_iter_children(self, parent):
        """Overridable.

        :Returns:
            The first child of parent or None if parent has no children.
            If parent is None, return the first node of the model.
        """
        raise NotImplementedError

    def on_iter_has_child(self, node):
        """Overridable.

        :Returns:
            True if the given node has children.
        """
        raise NotImplementedError

    def on_iter_n_children(self, node):
        """Overridable.

        :Returns:
            The number of children for the given node. If node is None,
            return the number of top level nodes.
        """
        raise NotImplementedError

    def on_iter_nth_child(self, parent, n):
        """Overridable.

        :Parameters:
            parent : object
            n : int
                Index of child within parent.

        :Returns:
            The child for the given parent index starting at 0. If parent None,
            return the top level node corresponding to "n".
            If "n" is larger then available nodes, return None.
        """
        raise NotImplementedError

    def on_iter_parent(self, child):
        """Overridable.

        :Returns:
            The parent node of child or None if child is a top level node."""
        raise NotImplementedError

    def on_ref_node(self, node):
        raise NotImplementedError

    def on_unref_node(self, node):
        raise NotImplementedError
