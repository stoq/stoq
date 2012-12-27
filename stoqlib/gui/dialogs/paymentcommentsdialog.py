import datetime

from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.lib.translation import stoqlib_gettext as _


class PaymentCommentsListSlave(ModelListSlave):
    model_type = PaymentComment
    columns = [
        Column('date', title=_('Date'),
               data_type=datetime.date, width=100),
        Column('author.person.name', title=_('Author'),
               width=150, data_type=str),
        Column('comment', title=_('Comment'),
               data_type=str, expand=True),
    ]

    def populate(self):
        return self.parent.payment.comments or []

    def run_editor(self, store, model):
        if not model:
            model = PaymentComment(author=api.get_current_user(store),
                                   payment=store.fetch(self.parent.payment),
                                   comment=u"",
                                   store=store)
        return self.run_dialog(
            NoteEditor,
            store=store,
            model=model,
            attr_name="comment",
            title=_(u"Payment Comment"))


class PaymentCommentsDialog(ModelListDialog):
    list_slave_class = PaymentCommentsListSlave
    title = _(u'Payment Comments')
    size = (600, 250)

    def __init__(self, store, payment):
        self.payment = payment
        ModelListDialog.__init__(self, store)
