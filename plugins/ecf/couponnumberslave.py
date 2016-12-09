# -*-  Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2016 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##


from kiwi.ui.forms import TextField

from stoqlib.database.viewable import Viewable
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CouponNumberSlave(BaseEditorSlave):
    model_type = Viewable

    @cached_property()
    def fields(self):
        return dict(
            coupon_id=TextField(_('Coupon Number'), proxy=True, editable=False,
                                widget_data_type=int),
        )

    def on_attach(self, parent):
        parent.right_labels_sizegroup.add_widget(self.coupon_id_lbl)
        parent.right_values_sizegroup.add_widget(self.coupon_id)
