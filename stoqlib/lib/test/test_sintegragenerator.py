import datetime

from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_branch

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.lib.sintegragenerator import StoqlibSintegraGenerator
from stoqlib.lib.test.test_sintegra import compare_sintegra_file

class TestSintegraGenerator(DomainTest):

    def testRecevingOrder(self):
        order = self.create_receiving_order()
        order.receival_date = datetime.date(2007, 6, 1)
        order.discount_value = 10
        #order.purchase.discount_value = 5
        #order.purchase.surcharge_value = 8
        #order.surcharge_value = 15
        order.ipi_total = 10
        order.freight_total = 6
        order.secure_value = 6
        order.expense_value = 12
        supplier = self.create_supplier()
        company = supplier.person.has_individual_or_company_facets()
        company.state_registry = '103238426117'
        order.supplier = supplier
        employee = self.create_employee()
        branch = get_current_branch(self.trans)
        branch.manager = employee

        order.purchase.status = order.purchase.ORDER_PENDING

        sellable = self.create_sellable()
        sellable.tax_constant = SellableTaxConstant(
            description="18",
            tax_type=int(TaxType.CUSTOM),
            tax_value=18,
            connection=self.trans)
        self.create_receiving_order_item(order, sellable=sellable)

        sellable2 = self.create_sellable()
        sellable2.tax_constant = SellableTaxConstant(
            description="6",
            tax_type=int(TaxType.CUSTOM),
            tax_value=6,
            connection=self.trans)
        self.create_receiving_order_item(order, sellable=sellable2)

        order.purchase.confirm()
        order.set_valid()
        order.confirm()

        sellable.id = 9999
        sellable2.id = 10000

        generator = StoqlibSintegraGenerator(self.trans,
                                             datetime.date(2007, 6, 1),
                                             datetime.date(2007, 6, 30))

        compare_sintegra_file(generator.sintegra, 'sintegra-receival')
