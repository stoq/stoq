#!/usr/bin/env python
from sys import path
path.insert(0, "..")

from stoqlib.reporting.base.utils import build_report, print_preview
from stoqlib.reporting.base.printing import ReportTemplate
from stoqlib.reporting.base.tables import TableColumn as TC

class ClientsReport(ReportTemplate):
    """ Sample column table report. If we have to set a fixed size to our columns
    and allow some interesting resources such truncate parameter, a table
    column should be a good idea. Once we defined table column instances, we
    must call a column table report to use it.
      """
    def __init__(self, filename, **args):
        report_name = 'Sample Clients Report'
        ReportTemplate.__init__(self, filename, report_name, do_header=0)
        rows = self.get_rows()
        self.add_column_table(rows, self.get_cols())
        self.add_paragraph('%d clients listed.' % len(rows),
                           style='Normal-AlignRight')

    def get_cols(self):
        cols = [TC("Id", width=35),
                TC("Name", expand=True),
                TC("District", width=80),
                TC("City", width=80),
                TC("State", width=50),
                TC("Birth date", width=85)]
        return cols

    def get_rows(self):
        clients = []
        for data in open('csv/clients.csv').readlines():
            data = data.split("\t")
            id = int(data[0])
            name = data[1]
            district = data[2]
            city = data[3]
            state = data[4]
            birth_date = data[5]
            columns = [id, name, district, city, state, birth_date]

            clients.append(columns)
        # Columns will be sorted by id
        clients.sort()
        return clients

if __name__ == "__main__":
    report_filename = build_report(ClientsReport)
    print_preview(report_filename)
