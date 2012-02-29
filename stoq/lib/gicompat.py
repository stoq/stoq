import sys


def install_enum(mod, enum):
    modname = mod.__name__.rsplit('.', 1)[1].upper()
    for value, enum in enum.__enum_values__.items():
        name = enum.value_name
        name = name.replace(modname + '_', '')
        setattr(mod, name, enum)


def install_flags(mod, flags):
    modname = mod.__name__.rsplit('.', 1)[1].upper()
    for value, flag in flags.__flags_values__.items():
        for name in flag.value_names:
            name = name.replace(modname + '_', '')
            setattr(mod, name, flag)


def enable():
    try:
        import gi
    except ImportError, e:
        print e
        return False

    # gobject
    from gi.repository import GObject
    sys.modules['gobject'] = GObject
    from gi._gobject import propertyhelper
    sys.modules['gobject.propertyhelper'] = propertyhelper

    # atk
    gi.require_version('Atk', '1.0')
    from gi.repository import Atk
    sys.modules['gtk'] = Atk

    # pango
    gi.require_version('Pango', '1.0')
    from gi.repository import Pango
    sys.modules['pango'] = Pango

    # pangocairo
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import PangoCairo
    sys.modules['pangocairo'] = PangoCairo

    # poppler
    gi.require_version('Poppler', '0.18')
    from gi.repository import Poppler
    sys.modules['poppler'] = Poppler

    # gdk
    gi.require_version('Gdk', '2.0')
    from gi.repository import Gdk
    sys.modules['gtk.gdk'] = Gdk
    for enum_type in [Gdk.CursorType,
                      Gdk.WindowTypeHint]:
        install_enum(Gdk, enum_type)
    for flags_type in [Gdk.EventMask,
                       Gdk.ModifierType]:
        install_flags(Gdk, flags_type)
    Gdk.BUTTON_PRESS = 4

    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import GdkPixbuf
    Gdk.Pixbuf = GdkPixbuf.Pixbuf
    Gdk.pixbuf_new_from_file = GdkPixbuf.Pixbuf.new_from_file

    # gtk
    gi.require_version('Gtk', '2.0')
    from gi.repository import Gtk
    sys.modules['gtk'] = Gtk
    Gtk.gdk = Gdk
    Gtk.settings_get_default = Gtk.Settings.get_default

    Gtk.pygtk_version = (2, 99, 0)

    Gtk.gtk_version = (2, 22, 0)
    for enum_type in [Gtk.ArrowType,
                      Gtk.ButtonsType,
                      Gtk.Justification,
                      Gtk.IconSize,
                      Gtk.MessageType,
                      Gtk.Orientation,
                      Gtk.PackType,
                      Gtk.PolicyType,
                      Gtk.PositionType,
                      Gtk.ResponseType,
                      Gtk.SelectionMode,
                      Gtk.ShadowType,
                      Gtk.SizeGroupMode,
                      Gtk.SortType,
                      Gtk.StateType,
                      Gtk.TextDirection,
                      Gtk.TreeViewColumnSizing,
                      Gtk.WindowPosition,
                      Gtk.WindowType]:
        install_enum(Gtk, enum_type)
    for flags_type in [Gtk.DialogFlags]:
        install_flags(Gtk, flags_type)

    class GenericCellRenderer(Gtk.CellRenderer):
        pass
    Gtk.GenericCellRenderer = GenericCellRenderer

    Gtk.image_new_from_stock = Gtk.Image.new_from_stock
    Gtk.expander_new_with_mnemonic = Gtk.Expander.new_with_mnemonic
    Gtk.widget_get_default_direction = Gtk.Widget.get_default_direction
    Gtk.icon_theme_get_default = Gtk.IconTheme.get_default

    # box
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

    # vte
    gi.require_version('Vte', '0.0')
    from gi.repository import Vte
    sys.modules['vte'] = Vte

    return True
