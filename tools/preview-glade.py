#!/usr/bin/env python

import sys

import gtk
from kiwi.ui.hyperlink import HyperLink
from kiwi.ui.objectlist import ObjectList, ObjectTree
from kiwi.ui.widgets.label import ProxyLabel
from kiwi.ui.widgets.combo import ProxyComboEntry, ProxyComboBox
from kiwi.ui.widgets.checkbutton import ProxyCheckButton
from kiwi.ui.widgets.radiobutton import ProxyRadioButton
from kiwi.ui.widgets.entry import ProxyEntry, ProxyDateEntry
from kiwi.ui.widgets.spinbutton import ProxySpinButton
from kiwi.ui.widgets.textview import ProxyTextView
from kiwi.ui.widgets.button import ProxyButton


# pyflakes
HyperLink
ObjectList
ObjectTree
ProxyButton
ProxyLabel
ProxyComboEntry
ProxyComboBox
ProxyCheckButton
ProxyRadioButton
ProxyEntry
ProxyDateEntry
ProxySpinButton
ProxyTextView


def main(args):
    if len(args) < 2:
        print 'ERROR: need a filename'
        return

    b = gtk.Builder()
    b.add_from_file(args[1])

    for o in b.get_objects():
        if isinstance(o, gtk.Window):
            o.connect('destroy', gtk.main_quit)
            o.show()

    gtk.main()

if __name__ == '__main__':
    main(sys.argv)
