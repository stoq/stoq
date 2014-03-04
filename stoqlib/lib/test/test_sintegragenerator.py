from stoqdrivers.enum import TaxType

from stoqlib.database.runtime import get_current_branch

from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.inventory import InventoryItem
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.sellable import SellableTaxConstant
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.dateutils import localdate
from stoqlib.lib.sintegragenerator import StoqlibSintegraGenerator
from stoqlib.lib.test.test_sintegra import compare_sintegra_file


class TestSintegraGenerator(DomainTest):

    def test_registers(self):
        order = self.create_receiving_order()
        order.receival_date = localdate(2007, 6, 1)
        order.discount_value = 10
        # order.purchase.discount_value = 5
        # order.purchase.surcharge_value = 8
        # order.surcharge_value = 15
        order.ipi_total = 10
        order.freight_total = 6
        order.secure_value = 6
        order.expense_value = 12
        supplier = self.create_supplier()
        company = supplier.person.has_individual_or_company_facets()
        company.state_registry = u'103238426117'
        order.supplier = supplier
        employee = self.create_employee()
        branch = get_current_branch(self.store)
        branch.manager = employee

        purchase = order.purchase_orders.find()[0]
        purchase.status = purchase.ORDER_PENDING

        sellable = self.create_sellable()
        sellable.tax_constant = SellableTaxConstant(
            description=u"18",
            tax_type=int(TaxType.CUSTOM),
            tax_value=18,
            store=self.store)
        self.create_receiving_order_item(order, sellable=sellable)

        sellable2 = self.create_sellable()
        sellable2.tax_constant = SellableTaxConstant(
            description=u"6",
            tax_type=int(TaxType.CUSTOM),
            tax_value=6,
            store=self.store)
        self.create_receiving_order_item(order, sellable=sellable2)

        purchase.confirm()
        order.confirm()

        sellable.code = u'9999'
        sellable2.code = u'10000'

        sale = self.create_sale()
        sale.open_date = localdate(2007, 6, 10)

        sellable3 = self.create_sellable()
        product = sellable3.product
        sellable.tax_constant = SellableTaxConstant(
            description=u"18",
            tax_type=int(TaxType.CUSTOM),
            tax_value=18,
            store=self.store)

        sale.add_sellable(sellable3, quantity=1)

        self.create_storable(product, get_current_branch(self.store), stock=100)

        sale.order()

        method = PaymentMethod.get_by_name(self.store, u'money')
        method.create_payment(Payment.TYPE_IN, sale.group, sale.branch,
                              sale.get_sale_subtotal())

        sale.confirm()
        sale.group.pay()
        sale.close_date = localdate(2007, 6, 10)
        sale.confirm_date = localdate(2007, 6, 10)
        sellable3.code = u'09999'

        inventory = self.create_inventory(branch=branch)
        inventory.open_date = localdate(2007, 6, 15)

        # product came from sellable3
        inventory_item = InventoryItem(product=product,
                                       product_cost=product.sellable.cost,
                                       inventory=inventory,
                                       recorded_quantity=99,
                                       store=self.store)
        inventory_item.cfop_data = self.store.find(CfopData).order_by(CfopData.code).first()
        inventory_item.reason = u'Test'
        inventory_item.actual_quantity = 99
        inventory_item.counted_quantity = 99
        inventory_item.adjust(invoice_number=999)
        inventory.close()
        inventory.close_date = localdate(2007, 6, 15)

        generator = StoqlibSintegraGenerator(self.store,
                                             localdate(2007, 6, 1),
                                             localdate(2007, 6, 30))

        try:
            compare_sintegra_file(generator.sintegra, 'sintegra-receival')
        except AssertionError as e:
            self.fail(e)
