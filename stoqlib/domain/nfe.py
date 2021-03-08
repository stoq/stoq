# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal

from storm.expr import And
from storm.references import Reference, ReferenceSet

from stoqlib.database.properties import (BoolCol, DateTimeCol, IdCol, IntCol,
                                         PriceCol, QuantityCol, UnicodeCol,
                                         XmlCol)
from stoqlib.database.runtime import set_current_branch_station
from stoqlib.domain.address import CityLocation
from stoqlib.domain.base import Domain
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person, Supplier
from stoqlib.domain.product import Product, ProductComponent
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.receiving import ReceivingInvoice, ReceivingOrder
from stoqlib.domain.sellable import Sellable
from stoqlib.exceptions import SellableError
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class NFePurchase(Domain):
    __storm_table__ = 'nfe_purchase'

    user_id = IdCol()

    #: The user responsible for the import
    user = Reference(user_id, "LoginUser.id")
    branch_id = IdCol()

    #: The branch that is buying/receiving the products
    branch = Reference(branch_id, "Branch.id")

    nfe_supplier_id = IdCol()

    #: The supplier of the products
    nfe_supplier = Reference(nfe_supplier_id, "NFeSupplier.id")

    purchase_order_id = IdCol()

    #: Reference the purchase order when the importing is done
    purchase_order = Reference(purchase_order_id, "PurchaseOrder.id")

    #: The CNPJ of the branch that is importing the nfe
    cnpj = UnicodeCol(default=u"")

    #: Invoice number
    invoice_number = IntCol()

    #: Invoice series
    invoice_series = IntCol()

    #: Stores the date that this nfe was imported
    process_date = DateTimeCol(default_factory=localnow)

    #: If this purchase is already confirmed
    confirm_purchase = BoolCol(default=False)

    #: Freight type can be FOB and CIF
    freight_type = UnicodeCol(default=u"fob")

    #: The price of the freight
    freight_cost = PriceCol()

    #: The total cost of products + services
    total_cost = PriceCol()

    #: The Raw NFe's XML
    xml = XmlCol()

    payments = ReferenceSet('id', 'NFePayment.nfe_purchase_id')

    @property
    def supplier_name(self):
        return self.nfe_supplier.name or self.nfe_supplier.fancy_name

    @property
    def branch_description(self):
        return self.branch.get_description()

    @property
    def freight_type_str(self):
        if self.freight_type == PurchaseOrder.FREIGHT_FOB:
            return u"FOB"
        return u"CIF"

    @property
    def items(self):
        items = self.store.find(NFeItem, NFeItem.nfe_purchase == self)
        return items

    @classmethod
    def find_purchase_order(cls, store, nfe_supplier, invoice_number, invoice_series):
        return store.find(NFePurchase,
                          And(NFePurchase.nfe_supplier == nfe_supplier,
                              NFePurchase.invoice_number == invoice_number,
                              NFePurchase.invoice_series == invoice_series)).one()

    # Private Methods

    def _create_payment_group(self):
        return PaymentGroup(store=self.store,
                            recipient=self.nfe_supplier.supplier.person,
                            payer=self.branch.person)

    def _create_and_confirm_purchase_order(self, identifier, payment_group, notes, station,
                                           responsible):
        self.purchase_order = PurchaseOrder(store=self.store,
                                            identifier=identifier,
                                            branch=self.branch,
                                            status=PurchaseOrder.ORDER_PENDING,
                                            open_date=localnow(),
                                            notes=notes,
                                            freight_type=self.freight_type,
                                            expected_freight=self.freight_cost,
                                            supplier=self.nfe_supplier.supplier,
                                            group=payment_group,
                                            station=station)
        self._add_purchase_order_item()
        self.purchase_order.confirm(responsible=responsible)

    def _add_purchase_order_item(self):
        for item in self.items:
            sellable = item.sellable
            purchase_item = self.purchase_order.add_item(sellable=sellable,
                                                         quantity=item.quantity,
                                                         cost=item.cost,
                                                         ipi_value=item.ipi_cost,
                                                         icms_st_value=item.icmsst_cost)

            item.purchase_item_id = purchase_item.id
            sellable.product.ncm = item.ncm or sellable.product.ncm
            self.maybe_create_product_supplier_info(item, self.nfe_supplier.supplier)

            product = sellable.product
            if product and product.is_package:
                for component in product.get_components():
                    self.purchase_order.add_item(sellable=component.component.sellable,
                                                 # The real cost and quantity will be
                                                 # calculated from the parent item
                                                 cost=item.cost, quantity=item.quantity,
                                                 parent=purchase_item)

    def _create_payments(self, station):
        nfe_payments = list(self.payments)
        # FIXME: receive from frontend
        method = PaymentMethod.get_by_name(store=self.store, name=u"bill")

        # FIXME: Select method in frontend and add option to split the payment
        # in more than one duplicate
        identifier = Payment.get_temporary_identifier(self.store)
        if not nfe_payments:
            payment = method.create_payment(branch=self.purchase_order.branch,
                                            station=station,
                                            payment_type=Payment.TYPE_OUT,
                                            payment_group=self.purchase_order.group,
                                            value=self.purchase_order.purchase_total,
                                            identifier=identifier)
            payment.status = u'paid'
            return payment

        payments = []
        for i, item in enumerate(nfe_payments, start=1):
            identifier = Payment.get_temporary_identifier(self.store)
            payment = Payment(store=self.store,
                              branch=self.purchase_order.branch,
                              identifier=identifier,
                              value=item.value,
                              base_value=item.value,
                              due_date=item.due_date,
                              status=Payment.STATUS_PAID,
                              group=self.purchase_order.group,
                              method=method,
                              bill_received=True,
                              payment_type=Payment.TYPE_OUT,
                              station=station)
            payment.description = method.describe_payment(payment.group, i,
                                                          len(list(nfe_payments)))
            item.description = payment.description
            self.purchase_order.group.add_item(payment)
            payments.append(payment)

        return payments

    #
    # Public
    #

    def get_key(self):
        if self.xml is None:
            return

        inf_nfe = self.xml.find('.//{*}infNFe')
        # Removing prefix NFe from the actual Id
        key = inf_nfe.get('Id')[3:]
        return key

    def find_or_create_supplier(self, nfe_supplier):
        # FIXME: Need to do the same thing to Individual suppliers
        person = Person.get_or_create_by_document(self.store, nfe_supplier.cnpj,
                                                  name=nfe_supplier.name,
                                                  phone_number=nfe_supplier.phone_number,
                                                  notes=u"Automatically created by Stoq-Link")

        person.company.state_registry = nfe_supplier.state_registry
        person.company.fancy_name = nfe_supplier.fancy_name or nfe_supplier.name

        if person.supplier is None:
            supplier = Supplier(store=self.store, person=person)
            nfe_supplier.supplier = supplier

        return person.supplier

    def create_purchase_order(self, responsible, create_payments=False,
                              station_name=u'StoqLinkServer'):
        payment_group = self._create_payment_group()
        identifier = PurchaseOrder.get_temporary_identifier(self.store)
        notes = _(u"Invoice number: %s") % self.invoice_number
        station = set_current_branch_station(self.store, station_name, confirm=False)
        self._create_and_confirm_purchase_order(identifier,
                                                payment_group,
                                                notes,
                                                station,
                                                responsible)
        if create_payments:
            self._create_payments(station)

        self.create_receiving_order(station)
        self.store.commit()

        return self.purchase_order

    def create_receiving_order(self, station):
        notes = u"Created automatically with Stoq-Link"
        # TODO Eventually get this from the invoice data.
        cfop = sysparam.get_object(self.store, 'DEFAULT_RECEIVING_CFOP')
        receiving_invoice = ReceivingInvoice(store=self.store,
                                             freight_total=self.freight_cost,
                                             invoice_number=self.invoice_number,
                                             invoice_total=self.total_cost,
                                             supplier=self.purchase_order.supplier,
                                             branch=self.branch,
                                             responsible=self.user,
                                             station=station)

        receiving_order = ReceivingOrder(store=self.store,
                                         branch=self.branch,
                                         station=station,
                                         notes=notes,
                                         cfop=cfop,
                                         confirm_date=datetime.datetime.now(),
                                         status=u'closed',
                                         receiving_invoice=receiving_invoice)

        receiving_order.add_purchase(self.purchase_order)
        for item in self.purchase_order.get_items():
            receiving_order.add_purchase_item(item=item)

        if self.freight_type == PurchaseOrder.FREIGHT_CIF:
            receiving_order.update_payments(create_freight_payment=True)

        receiving_invoice.freight_type = receiving_invoice.guess_freight_type()
        receiving_order.confirm(self.user)

        return receiving_order

    def maybe_create_product_supplier_info(self, nfe_item, supplier):
        from stoqlib.domain.product import ProductSupplierInfo
        product = nfe_item.sellable.product
        info = product.get_product_supplier_info(supplier, self.branch)

        if not info:
            info = ProductSupplierInfo(store=self.store,
                                       product=nfe_item.sellable.product,
                                       supplier_code=nfe_item.supplier_code,
                                       supplier=supplier,
                                       branch=self.branch)

        info.base_cost = Decimal(nfe_item.cost)
        extra_cost = nfe_item.ipi_cost + nfe_item.icmsst_cost
        nfe_item.sellable.cost = info.base_cost + extra_cost

    def create_sellable(self, product_info, responsible):
        if product_info.get('is_package') != 'true':
            raise SellableError(
                """A criação de produtos somente é permitida para produtos do tipo pacote.
                Verifique o cache do seu navegador.""")

        sellable = None
        if product_info["code"]:
            sellable = self.store.find(Sellable,
                                       Sellable.code == product_info["code"])
        if sellable:
            return

        sellable = Sellable(store=self.store,
                            description=product_info["description"],
                            cost=Decimal(product_info["cost"]),
                            price=Decimal(product_info["price"]))

        sellable.code = product_info["code"]
        sellable.barcode = product_info["barcode"]
        sellable.notes = "Created via API" + product_info["notes"]
        sellable.unit_id = product_info["unit_id"] or None
        sellable.tax_constant_id = product_info["tax_constant"] or None
        sellable.default_sale_cfop_id = product_info["default_sale_cfop_id"] or None
        sellable.category_id = product_info["category_id"] or None
        # FIXME Need to get more info from NFe to fill both Product and Storable
        product = Product(store=self.store, sellable=sellable)
        product.manage_stock = product_info.get('manage_stock') == 'true'
        product.is_package = product_info.get('is_package') == 'true'
        package_quantity = product_info.get('package_quantity')
        item_ean = product_info.get('item_ean')
        item = self.store.find(Sellable, barcode=item_ean).one()
        ProductComponent(product=product,
                         component=item.product,
                         price=sellable.get_price(),
                         quantity=Decimal(package_quantity))
        return sellable


class NFeSupplier(Domain):
    __storm_table__ = 'nfe_supplier'

    #: The CNPJ of the supplier
    cnpj = UnicodeCol(default=u"")

    #: The real name of the supplier
    name = UnicodeCol(default=u"")

    #: The fancy name of the supplier
    fancy_name = UnicodeCol(default=u"")

    #: Postal code
    postal_code = UnicodeCol(default=u"")

    #: Address commplement (ex: ap 22)
    complement = UnicodeCol(default=u"")

    #: The supplier district
    district = UnicodeCol(default=u"")

    #: The street/avenue name
    street = UnicodeCol(default=u"")

    #: Primary phone
    phone_number = UnicodeCol(default=u"")

    #: Street number
    street_number = IntCol()

    #: Municipal registry if have both product and service in the same invoice
    municipal_registry = UnicodeCol(default=u"")

    #: IBGE's State Code is national 2 digit registry (ex: 29 = Bahia)
    state_registry = UnicodeCol(default=u"")

    #: IBGE's City Code is national 7 digit registry (ex: 2927408 = Salvador)
    city_code = IntCol()

    #: Stoq supplier id
    supplier_id = IdCol()

    #: Stoq supplier reference
    supplier = Reference(supplier_id, "Supplier.id")

    @property
    def state(self):
        city_location = self.store.find(CityLocation,
                                        city_code=self.city_code).one()
        return city_location.state

    @property
    def country(self):
        city_location = self.store.find(CityLocation,
                                        city_code=self.city_code).one()
        return city_location.country


class NFeItem(Domain):
    __storm_table__ = "nfe_item"

    nfe_purchase_id = IdCol()
    nfe_purchase = Reference(nfe_purchase_id, "NFePurchase.id")

    sellable_id = IdCol()
    sellable = Reference(sellable_id, "Sellable.id")

    purchase_item_id = IdCol()
    purchase_item = Reference(purchase_item_id, "PurchaseItem.id")

    #: The internal code for this item
    code = UnicodeCol(default=u"")

    #: Barcode of this product
    barcode = UnicodeCol(default=u"")

    #: The suppliers code for this item
    supplier_code = UnicodeCol(default=u"")

    #: Description (or name) of the item in the invoice
    description = UnicodeCol(default=u"")

    #: Nomenclatura Comum do Mercosul or Common Numenclature of Mercosul
    ncm = UnicodeCol(default=u"")

    genero = UnicodeCol(default=u"")

    ex_tipi = UnicodeCol(default=u"")

    #: The price of purchase of this item
    cost = PriceCol()

    #: The discount value applied to this item
    discount_value = PriceCol()

    #: Number of items purchased
    quantity = QuantityCol()

    #: The total freight value for the item(s)
    freight_cost = PriceCol(default=0)

    #: The total insurance value for the item(s)
    insurance_cost = PriceCol(default=0)

    #: The total value of Substitution ICMC paid on the item(s)
    icmsst_cost = PriceCol(default=0)

    #: The total value of IPI paid on the item(s)
    ipi_cost = PriceCol(default=0)

    @property
    def sellable_description(self):
        if self.sellable:
            return self.sellable.description
        return ""

    @property
    def sellable_code(self):
        if self.sellable:
            return self.sellable.code
        return ""


class NFePayment(Domain):
    __storm_table__ = "nfe_payment"

    nfe_purchase_id = IdCol()
    nfe_purchase = Reference(nfe_purchase_id, "NFePurchase.id")
    method_id = IdCol()

    #: Payment method (ex: bill, credit card, etc)
    method = Reference(method_id, "PaymentMethod.id")

    #: The final value of the payment
    value = PriceCol()

    #: Installment number
    duplicate_number = UnicodeCol()

    #: The final date for the payment
    due_date = DateTimeCol(default=None)

    #: The description generated by the system for the payment
    description = UnicodeCol(default=u"")
