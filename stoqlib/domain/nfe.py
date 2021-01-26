# -*- encoding: utf8 -*-

from storm.references import Reference, ReferenceSet
from stoqlib.database.properties import (BoolCol, IntCol, DateTimeCol, UnicodeCol,
                                         PriceCol, QuantityCol, IdCol, XmlCol)
from stoqlib.domain.address import CityLocation
from stoqlib.lib.dateutils import localnow
from stoqlib.domain.base import Domain
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
