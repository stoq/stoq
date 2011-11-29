#!/usr/bin/env python
# -*- coding: utf-8 -*-

import operator

from stoqlib.reporting.base.utils import build_report, print_preview
from stoqlib.reporting.base.printing import ReportTemplate
from stoqlib.reporting.base.flowables import RIGHT, CENTER
from stoqlib.reporting.base.tables import ObjectTableColumn as OTC

class Product:
    def __init__(self, qty, unit, description, price):
        self.quantity = qty
        self.unit = unit
        self.description = description
        self.price = price
        self.total_value = qty * price

    def get_quantity(self):
        return '%.2f' % self.quantity

    def get_unit(self):
        return self.unit

    def get_description(self):
        return self.description.upper()

    def get_price(self):
        return '$ %.2f' % self.price

    def get_total_value(self):
        return '$ %.2f' % self.total_value

class PurchaseOrderReport(ReportTemplate):
    """ Sample object table report. For complex data that is stored in a
    list of objects, an object table is recommended.
      """
    def __init__(self, filename, **args):
        report_name = 'Purchase Order Report'
        ReportTemplate.__init__(self, filename, report_name, do_header=0)
        self.add_supplier_section()
        self.add_instruction_section()
        self.add_item_section()
        self.build_signatures()

    def add_supplier_section(self):
        self.add_title('Supplier')
        name  = 'Tigre S/A Tubos e Conexões'
        phone_number = '(47) 441-5366'
        contact  = 'Marcos Mascarenhas'
        self.add_data_table((('Name:', name),
                             ('Phone:', phone_number),
                             ('Contact:', contact)))

    def add_instruction_section(self):
        self.add_title('Instructions')
        self.add_blank_space()
        text = ('This order must be delivered until next month.\n'
                'Only three boxes will be allowed for a single product.\n'
                'A special protection will be provided for cement.')
        for line in text.split('\n'):
            if not line.strip():
                continue
            self.add_paragraph(line)
        self.add_blank_space()

    def add_item_section(self):
        self.add_title('Items')
        cols = [OTC("Qty", lambda o: o.get_quantity(), width=45,
                     align=RIGHT),
                OTC("Unit", lambda o: o.get_unit(), width=40, truncate=1),
                OTC("Description", lambda o: o.get_description(), width=150,
                    truncate=1),
                OTC("Price", lambda o: o.get_price(), width=80),
                OTC("Total value", lambda o: o.get_total_value(), width=80)]
        objects = self.get_objects()
        self.add_object_table(objects, cols, align=RIGHT)
        self.add_summary(objects)

    def add_summary(self, objects):
        self.add_paragraph('%d products listed.' % len(objects),
                           style='Normal-AlignRight')

        values = [object.total_value for object in objects]
        total_value = reduce(operator.add, values, 0.0)
        total_value = '$ %.2f' % total_value
        self.add_data_table((('Total value:', total_value), ),
                             align=RIGHT)

    def build_signatures(self):
        labels = ['Company manager', 'Purchase supervisor']
        self.add_signatures(labels, align=CENTER)


    def get_objects(self):
        products = []
        for data in open("csv/products.csv").readlines():
            data = data.split("\t")
            quantity = float(data[0])
            unit = data[1]
            description = data[2]
            price = float(data[3])
            product = Product(quantity, unit, description, price)
            products.append(product)
        return products

report_filename = build_report(PurchaseOrderReport)
print_preview(report_filename)
