#!/usr/bin/env python
# -*- coding: utf-8 -*-

from stoqlib.reporting.base.utils import print_preview, build_report
from stoqlib.reporting.base.printing import ReportTemplate

from stoqlib.reporting.base.tables import (ObjectTableColumn as OTC,
                                           RIGHT)

class ObjectTableColumnTest(ReportTemplate):
    report_name = "Simples teste com ObjectTableColumn"
    def __init__(self, filename, clients):
        ReportTemplate.__init__(self, filename,
                                self.report_name)
        self.add_title("Relatório de Clientes")
        self.add_object_table(clients, self.get_cols())

    def get_cols(self):
        return [OTC("Cod.", lambda obj: "%04d" % obj.id,
                    width=80, align=RIGHT),
                OTC("Nome", lambda obj: obj.name, width=400)]

class Client:
    def __init__(self, id, name):
        self.id, self.name = (id, name)

client_list = []
for i in range(35):
    client = Client(i, "Nome do cliente #%d" % i)
    client_list.append(client)

report_file = build_report(ObjectTableColumnTest, client_list)
print_preview(report_file)
