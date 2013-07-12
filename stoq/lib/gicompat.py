import ctypes
from ctypes import util
import os
import sys

Py_DecRef = lambda obj: ctypes.pythonapi.Py_DecRef(ctypes.py_object(obj))


def install_enums(mod, dest=None):
    from gi.repository import GObject  # pylint: disable=E0611

    if dest is None:
        dest = mod
    modname = dest.__name__.rsplit('.', 1)[1].upper()
    for attr in dir(mod):
        try:
            obj = getattr(mod, attr, None)
        except:
            continue
        try:
            if issubclass(obj, GObject.GEnum):
                for value, enum in obj.__enum_values__.items():
                    name = enum.value_name
                    name = name.replace(modname + '_', '')
                    setattr(dest, name, enum)
        except TypeError:
            continue
        try:
            if issubclass(obj, GObject.GFlags):
                for value, flag in obj.__flags_values__.items():
                    for name in flag.value_names:
                        name = name.replace(modname + '_', '')
                        setattr(dest, name, flag)
        except TypeError:
            continue


def enable():
    if os.environ['STOQ_USE_GI'] == '3.0':
        gtk_version = '3.0'
        webkit_version = '3.0'
    else:
        gtk_version = '2.0'
        webkit_version = '1.0'
    enable_gtk(version=gtk_version)
    enable_poppler()
    enable_webkit(version=webkit_version)
    enable_gudev()
    enable_vte()

    # glib
    from gi.repository import GLib  # pylint: disable=E0611
    sys.modules['glib'] = GLib

    # gobject
    from gi.repository import GObject  # pylint: disable=E0611
    GObject.GObjectMeta = GObject.GObject.__base__.__base__

    def set_data(self, key, value):
        if not hasattr(self, '__gobject_data'):
            self.__gobject_data = {}
        self.__gobject_data[key] = value
    GObject.GObject.set_data = set_data

    def get_data(self, key):
        if not hasattr(self, '__gobject_data'):
            self.__gobject_data = {}
        return self.__gobject_data[key]
    GObject.GObject.get_data = get_data

    sys.modules['gobject'] = GObject

    from gi._gobject import propertyhelper
    GObject.propertyhelper = propertyhelper
    sys.modules['gobject.propertyhelper'] = propertyhelper
    propertyhelper.property = propertyhelper.Property

    # gio
    from gi.repository import Gio  # pylint: disable=E0611
    sys.modules['gio'] = Gio

_unset = object()


def enable_gtk(version='2.0'):
    import gi
    # set the default encoding like PyGTK
    reload(sys)
    sys.setdefaultencoding('utf-8')

    from gi.repository import GLib  # pylint: disable=E0611

    # atk
    gi.require_version('Atk', '1.0')
    from gi.repository import Atk  # pylint: disable=E0611
    sys.modules['atk'] = Atk
    install_enums(Atk)

    # pango
    gi.require_version('Pango', '1.0')
    from gi.repository import Pango  # pylint: disable=E0611
    sys.modules['pango'] = Pango
    install_enums(Pango)

    # pangocairo
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import PangoCairo  # pylint: disable=E0611
    sys.modules['pangocairo'] = PangoCairo

    # gdk
    gi.require_version('Gdk', version)
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gdk  # pylint: disable=E0611
    from gi.repository import GdkPixbuf  # pylint: disable=E0611
    sys.modules['gtk.gdk'] = Gdk
    install_enums(Gdk)
    install_enums(GdkPixbuf, dest=Gdk)
    Gdk.BUTTON_PRESS = 4

    Gdk.Pixbuf = GdkPixbuf.Pixbuf
    Gdk.pixbuf_new_from_file = GdkPixbuf.Pixbuf.new_from_file
    Gdk.PixbufLoader = GdkPixbuf.PixbufLoader.new_with_type

    orig_get_frame_extents = Gdk.Window.get_frame_extents

    def get_frame_extents(window):
        try:
            try:
                rect = Gdk.Rectangle(0, 0, 0, 0)
            except TypeError:
                rect = Gdk.Rectangle()
            orig_get_frame_extents(window, rect)
        except TypeError:
            rect = orig_get_frame_extents(window)
        return rect
    Gdk.Window.get_frame_extents = get_frame_extents

    Gdk._2BUTTON_PRESS = 5

    # gtk
    gi.require_version('Gtk', version)
    from gi.repository import Gtk  # pylint: disable=E0611
    sys.modules['gtk'] = Gtk
    Gtk.gdk = Gdk

    Gtk.pygtk_version = (2, 99, 0)

    Gtk.gtk_version = (Gtk.MAJOR_VERSION,
                       Gtk.MINOR_VERSION,
                       Gtk.MICRO_VERSION)
    install_enums(Gtk)

    # Action
    class GActionClass(ctypes.Structure):
        _fields_ = [
            # GTypeClass
            ('g_type', ctypes.c_ulong),

            # GObjectClass
            ('construct_properties', ctypes.c_void_p),
            ('constructor', ctypes.c_void_p),
            ('set_property', ctypes.c_void_p),
            ('get_property', ctypes.c_void_p),
            ('dispose', ctypes.c_void_p),
            ('finalize', ctypes.c_void_p),
            ('dispatch_properties_changed', ctypes.c_void_p),
            ('notify', ctypes.c_void_p),
            ('pdummy', ctypes.c_void_p * 8),

            # GtkActionClass
            ('activate', ctypes.c_void_p),
            ('menu_item_type', ctypes.c_ulong),
            ('toolbar_item_type', ctypes.c_ulong),
        ]

    def get_library(name):
        path = util.find_library(name)
        if not path:
            raise ImportError('Could not find library "%s"' % name)
        return ctypes.cdll.LoadLibrary(path)

    # From pygtk gtk/gtk.override.py:
    # _wrap_gtk_action_set_tool_item_type
    def set_tool_item_type(menuaction, tool_item_type):
        if not issubclass(tool_item_type, Gtk.ToolItem):
            raise TypeError("argument must be a subtype of gtk.ToolItem")

        action_type = menuaction.__gtype__

        cgobject = get_library('gobject-2.0')
        # klass = (GtkActionClass *) g_type_class_ref(gtype);
        klass = ctypes.cast(
            cgobject.g_type_class_ref(hash(action_type)),
            ctypes.POINTER(GActionClass))

        # klass->toolbar_item_type = tool_item_type;
        klass.contents.toolbar_item_type = hash(tool_item_type.__gtype__)

        # g_type_class_unref(klass);
        cgobject.g_type_class_unref(klass)

    Gtk.Action.set_tool_item_type = classmethod(set_tool_item_type)

    # Alignment

    orig_Alignment = Gtk.Alignment

    class Alignment(orig_Alignment):
        def __init__(self, xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0):
            orig_Alignment.__init__(self)
            self.props.xalign = xalign
            self.props.yalign = yalign
            self.props.xscale = xscale
            self.props.yscale = yscale

    Gtk.Alignment = Alignment

    # Box

    orig_pack_end = Gtk.Box.pack_end

    def pack_end(self, child, expand=True, fill=True, padding=0):
        orig_pack_end(self, child, expand, fill, padding)
    Gtk.Box.pack_end = pack_end

    orig_pack_start = Gtk.Box.pack_start

    def pack_start(self, child, expand=True, fill=True, padding=0):
        orig_pack_start(self, child, expand, fill, padding)
    Gtk.Box.pack_start = pack_start

    # CellLayout

    orig_cell_pack_end = Gtk.CellLayout.pack_end

    def cell_pack_end(self, cell, expand=True):
        orig_cell_pack_end(self, cell, expand)
    Gtk.CellLayout.pack_end = cell_pack_end

    orig_cell_pack_start = Gtk.CellLayout.pack_start

    def cell_pack_start(self, cell, expand=True):
        orig_cell_pack_start(self, cell, expand)
    Gtk.CellLayout.pack_start = cell_pack_start

    orig_set_cell_data_func = Gtk.CellLayout.set_cell_data_func

    def set_cell_data_func(self, cell, func, user_data=_unset):
        def callback(*args):
            if args[-1] == _unset:
                args = args[:-1]
            return func(*args)
        orig_set_cell_data_func(self, cell, callback, user_data)
    Gtk.CellLayout.set_cell_data_func = set_cell_data_func

    # CellRenderer

    class GenericCellRenderer(Gtk.CellRenderer):
        pass
    Gtk.GenericCellRenderer = GenericCellRenderer

    from gi.repository import GObject  # pylint: disable=E0611

    # TreeModel
    def tree_model_foreach(treemodel, func):
        print('tree_model_foreach is not supported')
    Gtk.TreeModel.foreach = tree_model_foreach

    def _coerce_path(path):
        if isinstance(path, Gtk.TreePath):
            return path
        else:
            return Gtk.TreePath(path)

    orig_row_changed = Gtk.TreeModel.row_changed

    def row_changed(self, path, iter):
        return orig_row_changed(self, _coerce_path(path), iter)
    Gtk.TreeModel.row_changed = row_changed

    from .generictreemodel import GenericTreeModel  # pylint: disable=E0611
    Gtk.GenericTreeModel = GenericTreeModel

    # TreePath
    def gtk_tree_path_new(kls, cls, path=0):
        if isinstance(path, int):
            path = str(path)
        elif not isinstance(path, basestring):
            path = ":".join(str(val) for val in path)

        if len(path) == 0:
            raise TypeError("could not parse subscript '%s' as a tree path" % path)
        try:
            return cls.new_from_string(path)
        except TypeError:
            raise TypeError("could not parse subscript '%s' as a tree path" % path)

    Gtk.TreePath.__new__ = classmethod(gtk_tree_path_new)

    def gtk_tree_path_getitem(path, item):
        return path.get_indices()[item]

    Gtk.TreePath.__getitem__ = gtk_tree_path_getitem

    def gtk_tree_path_getiter(self):
        return iter(self.get_indices())

    Gtk.TreePath.__getiter__ = gtk_tree_path_getiter

    # ComboBox

    orig_combo_row_separator_func = Gtk.ComboBox.set_row_separator_func

    def combo_row_separator_func(self, func, user_data=_unset):
        def callback(*args):
            if args[-1] == _unset:
                args = args[:-1]
            return func(*args)
        orig_combo_row_separator_func(self, callback, user_data)
    Gtk.ComboBox.set_row_separator_func = combo_row_separator_func

    # Container

    def install_child_property(container, flag, pspec):
        print('install_child_property is not supported')
    Gtk.Container.install_child_property = classmethod(install_child_property)

    def container_child_get(container, child, name):
        # FIXME: hard coded list of known properties :(
        v = GObject.Value()
        v.init(int)
        container.child_get_property(child, name, v)
        return v.get_int(),
    Gtk.Container.child_get = container_child_get

    # EntryCompletion

    orig_completion_set_match_func = Gtk.EntryCompletion.set_match_func

    def completion_set_match_func(completion, func, data=None):
        return orig_completion_set_match_func(completion, func, data)
    Gtk.EntryCompletion.set_match_func = completion_set_match_func

    # GtkTextBuffer
    orig_text_buffer_get_text = Gtk.TextBuffer.get_text

    def text_buffer_get_text(text_buffer, start, end, include_hidden_chars=False):
        return orig_text_buffer_get_text(text_buffer, start, end,
                                         include_hidden_chars=False)
    Gtk.TextBuffer.get_text = text_buffer_get_text

    Gtk.expander_new_with_mnemonic = Gtk.Expander.new_with_mnemonic
    Gtk.icon_theme_get_default = Gtk.IconTheme.get_default
    Gtk.image_new_from_pixbuf = Gtk.Image.new_from_pixbuf
    Gtk.image_new_from_stock = Gtk.Image.new_from_stock
    Gtk.settings_get_default = Gtk.Settings.get_default
    Gtk.timeout_add = GLib.timeout_add
    Gtk.widget_get_default_direction = Gtk.Widget.get_default_direction
    Gtk.window_set_default_icon = Gtk.Window.set_default_icon
    Gtk.window_list_toplevels = Gtk.Window.list_toplevels

    def gtk_set_interactive(interactive):
        print('set_interactive is not supported')
    Gtk.set_interactive = gtk_set_interactive

    orig_gtk_widget_size_request = Gtk.Widget.size_request

    def gtk_widget_size_request(widget):
        size = orig_gtk_widget_size_request(widget)
        return size.width, size.height
    Gtk.Widget.size_request = gtk_widget_size_request

    class StyleItemGetter(object):
        def __init__(self, widget):
            self.widget = widget
            self.context = self.widget.get_style_context()

        def __getitem__(self, state):
            if state == Gtk.StateType.NORMAL:
                state = Gtk.StateFlags.NORMAL
            elif state == Gtk.StateType.INSENSITIVE:
                state = Gtk.StateFlags.INSENSITIVE
            color = self.context.get_background_color(state)
            return Gdk.Color(red=color.red,
                             green=color.green,
                             blue=color.blue)

    class Styles(object):
        def __init__(self, widget):
            self._widget = widget
            self.base = StyleItemGetter(widget)
            self.text = StyleItemGetter(widget)

    class StyleDescriptor(object):
        def __get__(self, instance, class_):
            return Styles(instance)
    Gtk.Widget.style = StyleDescriptor()

    Gtk.Widget.get_style = lambda self: self.style

    # gtk.unixprint
    class UnixPrint(object):
        pass
    unixprint = UnixPrint()
    sys.modules['gtkunixprint'] = unixprint

    # gtk.keysyms
    class Keysyms(object):
        pass
    keysyms = Keysyms()
    sys.modules['gtk.keysyms'] = keysyms
    Gtk.keysyms = keysyms
    for name in dir(Gdk):
        if name.startswith('KEY_'):
            target = name[4:]
            if target[0] in '0123456789':
                target = '_' + target
            value = getattr(Gdk, name)
            setattr(keysyms, target, value)


def enable_vte():
    import gi
    gi.require_version('Vte', '2.90')
    from gi.repository import Vte  # pylint: disable=E0611
    sys.modules['vte'] = Vte


def enable_poppler():
    import gi
    gi.require_version('Poppler', '0.18')
    from gi.repository import Poppler  # pylint: disable=E0611
    sys.modules['poppler'] = Poppler
    Poppler.pypoppler_version = (1, 0, 0)


def enable_webkit(version='1.0'):
    import gi
    gi.require_version('WebKit', version)
    from gi.repository import WebKit  # pylint: disable=E0611
    sys.modules['webkit'] = WebKit
    WebKit.WebView.get_web_inspector = WebKit.WebView.get_inspector


def enable_gudev():
    import gi
    gi.require_version('GUdev', '1.0')
    from gi.repository import GUdev  # pylint: disable=E0611
    sys.modules['gudev'] = GUdev
