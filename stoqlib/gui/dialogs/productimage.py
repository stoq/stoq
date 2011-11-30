import gettext

import gtk

from kiwi.ui.delegates import GladeDelegate
from kiwi.datatypes import converter
from stoqlib.gui.base.dialogs import RunnableView

_ = gettext.gettext

PIXBUF_CONVERTER = converter.get_converter(gtk.gdk.Pixbuf)


class ProductImageViewer(GladeDelegate, RunnableView):
    title = _("Product Image Viewer")
    gladefile = "ProductImageViewer"
    position = (0, 0)
    size = (325, 325)

    def __init__(self, *args, **kwargs):
        GladeDelegate.__init__(self, *args, **kwargs)
        self.toplevel.set_keep_above(True)
        self.toplevel.resize(*ProductImageViewer.size)
        self.toplevel.move(*ProductImageViewer.position)
        self.product = None
        self.toplevel.connect("configure-event", self._on_configure)

    def _on_configure(self, window, event):
        ProductImageViewer.position = event.x, event.y
        if (event.width != ProductImageViewer.size[0]
            or event.height != ProductImageViewer.size[1]):
            ProductImageViewer.size = event.width, event.height
            if self.product:
                self.set_product(self.product)

    def set_product(self, product):
        self.product = product
        if not product.full_image:
            self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR,
                                      gtk.ICON_SIZE_DIALOG)
        else:
            pixbuf = PIXBUF_CONVERTER.from_string(product.full_image)
            width, height = ProductImageViewer.size
            pixbuf = pixbuf.scale_simple(
                width, height, gtk.gdk.INTERP_BILINEAR)
            self.image.set_from_pixbuf(pixbuf)
