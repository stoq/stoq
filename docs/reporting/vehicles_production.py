#!/usr/bin/env python

from sys import path
path.insert(0, "..")

from stoqlib.reporting.utils import build_report, print_preview
from stoqlib.reporting.printing import ReportTemplate
from stoqlib.reporting.common import read_file, safe_int

class VehiclesProductionReport(ReportTemplate):
    """ Sample report table. Here we don't need columns because we already
    know the size of all the cells and it doesn't change. Special format
    routines are also not necessary in this case. So, one single header
    parameter and data list is everything we need.
      """
    def __init__(self, filename, **args):
        report_name = 'Vehicles Production Report'
        ReportTemplate.__init__(self, filename, report_name, timestamp=1,
                                leftMargin=30, topMargin=20,
                                rightMargin=30, do_header=0)
        rows = self.get_rows()
        self.run_report(rows)

    def run_report(self, production_list):
        header = ['Id','Description', 'Type', 'Control', 'Start M.',
                  'End M.', 'Total', 'Difference', 'Price', 'Total Price']
        rows = self.get_rows()
        self.add_report_table(rows, header=header)
        self.add_paragraph('%d itens listed' % len(rows),
                           style='Normal-AlignRight')

    def get_rows(self):
        production = []
        for data in read_file('csv/vehicles_production.csv'):
            id = safe_int(data[0])
            description = data[1]
            type = data[2]
            measurement = data[3]
            start_measurement = data[4]
            end_measurement = data[5]
            total = data[6]
            difference= data[7]
            price = data[8]
            total_value = data[9]
            columns = [id, description, type, measurement,
                       start_measurement, end_measurement,
                       total, difference, price, total_value]

            production.append(columns)
        # Columns will be sorted by id
        production.sort()
        return production

report_filename = build_report(VehiclesProductionReport)
print_preview(report_filename)
