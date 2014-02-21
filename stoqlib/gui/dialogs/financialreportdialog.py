""" Financial report dialog """

import datetime
import tempfile

import gtk

from stoqlib.database.queryexecuter import QueryExecuter
from stoqlib.domain.account import AccountTransaction
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.dialogs.spreadsheetexporterdialog import SpreadSheetExporter
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.financial import FinancialIntervalReport

_ = stoqlib_gettext


class FinancialReportDialog(BasicDialog):
    title = _('Financial Report Dialog')

    def __init__(self, store):
        self.store = store

        self.date_filter = DateSearchFilter(_('Year:'))
        self.date_filter.clear_options()
        self._populate_date_filter(self.date_filter)
        self.date_filter.select()
        self.date_filter.set_use_date_entries(False)

        BasicDialog.__init__(self, title=self.title)
        self.main_label.set_justify(gtk.JUSTIFY_CENTER)

        self.ok_button.set_label(_("Generate"))
        self.add(self.date_filter)
        self.date_filter.show()

    def confirm(self):
        start = self.date_filter.get_start_date()
        if start is None:
            warning(_("There are no transactions yet"))
            return

        f = FinancialIntervalReport(self.store, start.year)
        if not f.run():
            return
        temporary = tempfile.NamedTemporaryFile(
            # Translators: This will be part of a filename
            prefix=_('stoq-yearly-report'),
            suffix='.xls', delete=False)
        f.write(temporary)
        sse = SpreadSheetExporter()
        sse.export_temporary(temporary)

        self.close()
        self.temporary = temporary

    #
    # Private
    #

    def _populate_date_filter(self, date_filter):
        transaction = self.store.find(AccountTransaction).order_by(
            AccountTransaction.date).first()
        if transaction is None:
            return

        for i in range(transaction.date.year,
                       localtoday().year + 1):
            year = datetime.datetime(i, 1, 1)
            date_filter.add_option_fixed_interval(
                _('Year %d') % (i, ),
                year, year.replace(month=12, day=31),
                position=0)

    def _date_filter_query(self, search_spec, column):
        executer = QueryExecuter(self.store)
        executer.set_filter_columns(self.date_filter, [column])
        executer.set_search_spec(search_spec)
        return executer.search([self.date_filter.get_state()])
