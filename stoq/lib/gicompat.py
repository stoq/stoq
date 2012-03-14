import sys

import gi
from gi.repository import GObject


def install_enums(mod, dest=None):
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
    # gobject
    from gi.repository import GLib
    sys.modules['glib'] = GLib

    # gobject
    from gi.repository import GObject
    sys.modules['gobject'] = GObject
    from gi._gobject import propertyhelper
    sys.modules['gobject.propertyhelper'] = propertyhelper

    # gio
    from gi.repository import Gio
    sys.modules['gio'] = Gio

_unset = object()


def enable_gtk(version='2.0'):
    # set the default encoding like PyGTK
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # atk
    gi.require_version('Atk', '1.0')
    from gi.repository import Atk
    sys.modules['atk'] = Atk
    install_enums(Atk)

    # pango
    gi.require_version('Pango', '1.0')
    from gi.repository import Pango
    sys.modules['pango'] = Pango
    install_enums(Pango)

    # pangocairo
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import PangoCairo
    sys.modules['pangocairo'] = PangoCairo

    # gdk
    gi.require_version('Gdk', version)
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gdk
    from gi.repository import GdkPixbuf
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
    from gi.repository import Gtk
    sys.modules['gtk'] = Gtk
    Gtk.gdk = Gdk

    Gtk.pygtk_version = (2, 99, 0)

    Gtk.gtk_version = (Gtk.MAJOR_VERSION,
                       Gtk.MINOR_VERSION,
                       Gtk.MICRO_VERSION)
    install_enums(Gtk)

    # Action

    def set_tool_item_type(menuaction, gtype):
        print 'set_tool_item_type is not supported'
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
        print 'install_child_property is not supported'
    Gtk.Container.install_child_property = classmethod(install_child_property)

    Gtk.expander_new_with_mnemonic = Gtk.Expander.new_with_mnemonic
    Gtk.icon_theme_get_default = Gtk.IconTheme.get_default
    Gtk.image_new_from_pixbuf = Gtk.Image.new_from_pixbuf
    Gtk.image_new_from_stock = Gtk.Image.new_from_stock
    Gtk.settings_get_default = Gtk.Settings.get_default
    Gtk.widget_get_default_direction = Gtk.Widget.get_default_direction
    Gtk.window_set_default_icon = Gtk.Window.set_default_icon

    class BaseGetter(object):
        def __init__(self, widget):
            self.widget = widget
            self.context = self.widget.get_style_context()

        def __getitem__(self, state):
            color = self.context.get_background_color(state)
            return Gdk.Color(red=color.red,
                             green=color.green,
                             blue=color.blue)

    class Styles(object):
        def __init__(self, widget):
            self._widget = widget
            self.base = BaseGetter(widget)

    class StyleDescriptor(object):
        def __get__(self, instance, class_):
            return Styles(instance)
    Gtk.Widget.style = StyleDescriptor()

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
    gi.require_version('Vte', '0.0')
    from gi.repository import Vte
    sys.modules['vte'] = Vte


def enable_poppler():
    gi.require_version('Poppler', '0.18')
    from gi.repository import Poppler
    sys.modules['poppler'] = Poppler
    Poppler.pypoppler_version = (1, 0, 0)


def enable_webkit(version='1.0'):
    gi.require_version('WebKit', version)
    from gi.repository import WebKit
    sys.modules['webkit'] = WebKit
    WebKit.WebView.get_web_inspector = WebKit.WebView.get_inspector


def enable_gudev():
    gi.require_version('GUdev', '1.0')
    from gi.repository import GUdev
    sys.modules['gudev'] = GUdev
