import datetime

from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.comment import PaymentComment
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.lib.translation import stoqlib_gettext as _


class PaymentCommentsDialog(ModelListDialog):
    model_type = PaymentComment
    title = _(u'Payment Comments')
    size = (600, 250)

    columns = [
        Column('date', title=_('Date'),
               data_type=datetime.date, width=100),
        Column('author.person.name', title=_('Author'),
               width=150, data_type=str),
        Column('comment', title=_('Comment'),
               data_type=str, expand=True),
    ]

    def __init__(self, conn, payment):
        self.payment = payment
        self.conn = conn
        ModelListDialog.__init__(self, conn)

    def populate(self):
        return self.payment.comments or []

    def run_editor(self, trans, model):
        if not model:
            model = PaymentComment(author=api.get_current_user(trans),
                                   payment=trans.get(self.payment),
                                   comment=u"",
                                   connection=trans)
        return self.run_dialog(NoteEditor, trans, model,
                               "comment", _(u"Payment Comment"))
