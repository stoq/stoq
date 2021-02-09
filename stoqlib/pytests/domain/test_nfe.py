import datetime

import pytest

from stoqlib.domain.nfe import NFeItem, NFePayment, NFePurchase, NFeSupplier
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Person
from stoqlib.domain.product import ProductSupplierInfo
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.exceptions import SellableError


@pytest.fixture
def sellable(example_creator):
    return example_creator.create_sellable()


@pytest.fixture
def nfe_supplier(store, example_creator):
    supplier = example_creator.create_supplier()
    return NFeSupplier(store=store, supplier=supplier)


@pytest.fixture
def nfe_item(store, nfe_purchase):
    return NFeItem(store=store, nfe_purchase=nfe_purchase, cost=10)


@pytest.fixture
def nfe_purchase(store, current_branch, nfe_supplier):
    return NFePurchase(store=store, branch=current_branch, nfe_supplier=nfe_supplier,
                       invoice_number=2, invoice_series=1)


@pytest.fixture
def purchase_order(example_creator):
    return example_creator.create_purchase_order()


@pytest.fixture
def product_info(current_branch):
    return {
        "code": "123",
        "description": "Sellable Test",
        "price": 10,
        "cost": 5,
        "barcode": "123",
        "notes": "Test Notes",
        "tax_constant": None,
        "unit_id": None,
        "default_sale_cfop_id": None,
        "category_id": None,
        "manage_stock": "true",
        "is_package": "true",
        "package_quantity": 2,
        "item_ean": "123",
        "branch_id": current_branch.id,
        "product_quantity": None,
    }


@pytest.mark.parametrize('nfe_supplier_city_code', (1400472, 1400027, 1400175, 1400209))
def test_nfe_supplier_get_state(nfe_supplier, nfe_supplier_city_code):
    nfe_supplier.city_code = nfe_supplier_city_code

    assert nfe_supplier.state == 'RR'


@pytest.mark.parametrize('nfe_supplier_city_code', (1303569, 3203809, 3303500, 1718402))
def test_nfe_supplier_get_country(nfe_supplier, nfe_supplier_city_code):
    nfe_supplier.city_code = nfe_supplier_city_code

    assert nfe_supplier.country == 'Brazil'


def test_nfe_item_get_sellable_description_without_sellable(nfe_item):
    assert nfe_item.sellable_description == ""


@pytest.mark.parametrize('sellable_description', (
    'Shorts com Costuras', 'Casaco Vilan', 'Vestido Vadalena'))
def test_nfe_item_get_sellable_description_with_sellable(nfe_item, nfe_purchase,
                                                         sellable, sellable_description):
    sellable.description = sellable_description
    nfe_item.sellable = sellable
    nfe_item.nfe_purchase = nfe_purchase

    assert nfe_item.sellable_description == sellable.description


def test_nfe_item_get_sellable_code_without_sellable(nfe_item):
    assert nfe_item.sellable_code == ""


@pytest.mark.parametrize('sellable_code', ('15', '123', '230', '1595843695465'))
def test_nfe_item_get_sellable_code_with_sellable(nfe_item, nfe_purchase,
                                                  sellable, sellable_code):
    sellable.code = sellable_code
    nfe_item.sellable = sellable
    nfe_item.nfe_purchase = nfe_purchase

    assert nfe_item.sellable_code == sellable.code


@pytest.mark.parametrize('supplier_name', ('João', 'Pedro'))
def test_nfe_purchase_get_supplier_name_with_name(supplier_name, store, nfe_purchase):
    nfe_purchase.nfe_supplier.name = supplier_name
    assert nfe_purchase.supplier_name == supplier_name


@pytest.mark.parametrize('supplier_name', ('João', 'Pedro'))
def test_nfe_purchase_get_supplier_name_with_fancy_name(supplier_name, store, nfe_purchase):
    nfe_purchase.nfe_supplier.name = None
    nfe_purchase.nfe_supplier.fancy_name = supplier_name
    assert nfe_purchase.supplier_name == supplier_name


@pytest.mark.parametrize('fancy_name', ('Fancy Name', 'Another Fancy Name'))
def test_nfe_purchase_get_branch_description_with_company_fancy_name(fancy_name, nfe_purchase,
                                                                     current_branch):
    nfe_purchase.branch = current_branch
    current_branch.person.company.fancy_name = fancy_name
    assert nfe_purchase.branch_description == current_branch.person.company.fancy_name


@pytest.mark.parametrize('person_name', ('Person Name', 'Another Person Name'))
def test_nfe_purchase_get_branch_description_with_person_name(person_name, nfe_purchase,
                                                              current_branch):
    nfe_purchase.branch = current_branch
    current_branch.person.company.fancy_name = None
    current_branch.person.name = person_name

    assert nfe_purchase.branch_description == current_branch.person.name


def test_nfe_purchase_get_freight_type_str_fob(nfe_purchase):
    nfe_purchase.freight_type = PurchaseOrder.FREIGHT_FOB
    assert nfe_purchase.freight_type_str == "FOB"


def test_nfe_purchase_get_freight_type_str_cif(nfe_purchase):
    nfe_purchase.freight_type = PurchaseOrder.FREIGHT_CIF
    assert nfe_purchase.freight_type_str == "CIF"


def test_nfe_purchase_get_items(nfe_purchase, nfe_item):
    nfe_item.nfe_purchase = nfe_purchase
    assert set(nfe_purchase.items) == {nfe_item}


@pytest.mark.parametrize('invoice_number, invoice_series', ((1, 2), (666, 3), (333, 2)))
def test_nfe_purchase_find_purchase_order_empty(invoice_number, invoice_series,
                                                store, nfe_supplier):
    assert NFePurchase.find_purchase_order(
        store, nfe_supplier, invoice_number=invoice_number, invoice_series=invoice_series) is None


def test_nfe_purchase_find_puchase_order(nfe_purchase, nfe_supplier):
    nfe_purchase.invoice_series = 3
    nfe_purchase.invoice_number = 666
    nfe_purchase.nfe_supplier = nfe_supplier
    assert NFePurchase.find_purchase_order(
        nfe_purchase.store, nfe_supplier, invoice_number=666, invoice_series=3) is nfe_purchase


@pytest.mark.parametrize('invoice_series', (2, 4, 1))
def test_nfe_purchase_find_puchase_order_with_wrong_series(nfe_purchase, nfe_supplier,
                                                           invoice_series):
    nfe_purchase.invoice_series = 3
    nfe_purchase.invoice_number = 666
    nfe_purchase.nfe_supplier = nfe_supplier
    assert NFePurchase.find_purchase_order(
        nfe_purchase.store, nfe_supplier, invoice_number=666, invoice_series=invoice_series) is None


@pytest.mark.parametrize('invoice_number', (665, 667, 1))
def test_nfe_purchase_find_puchase_order_with_wrong_invoice_number(nfe_purchase, nfe_supplier,
                                                                   invoice_number):
    nfe_purchase.invoice_series = 3
    nfe_purchase.invoice_number = 666
    nfe_purchase.nfe_supplier = nfe_supplier
    assert NFePurchase.find_purchase_order(
        nfe_purchase.store, nfe_supplier, invoice_number=invoice_number, invoice_series=3) is None


def test_nfe_purchase_find_puchase_order_with_wrong_supplier(store, nfe_purchase, nfe_supplier):
    nfe_purchase.invoice_series = 3
    nfe_purchase.invoice_number = 666
    nfe_purchase.nfe_supplier = nfe_supplier
    wrong_nfe_supplier = NFeSupplier(store=store, cnpj='00.000.000/0000-00')
    assert NFePurchase.find_purchase_order(
        nfe_purchase.store, wrong_nfe_supplier, invoice_number=666, invoice_series=3) is None


def test_nfe_purchase_create_payment_group(nfe_purchase):
    group = nfe_purchase._create_payment_group()
    assert isinstance(group, PaymentGroup)
    assert group.recipient == nfe_purchase.nfe_supplier.supplier.person
    assert group.payer == nfe_purchase.branch.person


def test_nfe_purchase_create_and_confirm_purchase_order(
        nfe_purchase, current_user, current_station):
    assert nfe_purchase.purchase_order is None
    payment_group = nfe_purchase._create_payment_group()

    nfe_purchase._create_and_confirm_purchase_order(identifier=2, payment_group=payment_group,
                                                    notes='notes', station=current_station,
                                                    responsible=current_user)
    assert nfe_purchase.purchase_order.status == PurchaseOrder.ORDER_CONFIRMED


def test_nfe_purchase_test_add_purchase_order_item(store, nfe_purchase, nfe_item, nfe_supplier,
                                                   example_creator, sellable):
    purchase_order = example_creator.create_purchase_order()
    nfe_purchase.purchase_order = purchase_order
    sellable.product.is_package = False
    nfe_item.sellable = sellable
    nfe_item.nfe_purchase = nfe_purchase
    nfe_purchase.nfe_supplier = nfe_supplier
    nfe_purchase._add_purchase_order_item()

    assert len(list(nfe_purchase.purchase_order.get_items())) == 1


def test_nfe_purchase_test_add_purchase_order_item_with_package(
        store, nfe_purchase, nfe_item, nfe_supplier, example_creator, sellable):
    purchase_order = example_creator.create_purchase_order()
    nfe_purchase.purchase_order = purchase_order
    sellable.product.is_package = True
    nfe_item.sellable = sellable
    nfe_item.nfe_purchase = nfe_purchase
    nfe_item.quantity = 2
    nfe_purchase.nfe_supplier = nfe_supplier
    example_creator.create_product_component(product=sellable.product)
    nfe_purchase._add_purchase_order_item()

    assert len(list(nfe_purchase.purchase_order.get_items())) == 2


def test_nfe_purchase_test_create_payments(
        store, nfe_purchase, example_creator, current_station):
    nfe_purchase.purchase_order = example_creator.create_purchase_order()
    due_date = datetime.datetime.strptime('2020-12-03', "%Y-%m-%d")
    nfe_payment = NFePayment(store=store, nfe_purchase=nfe_purchase, due_date=due_date)
    payment = nfe_purchase._create_payments(current_station)

    assert len(payment) == 1
    assert payment[0].bill_received is True
    assert payment[0].due_date == nfe_payment.due_date


def test_nfe_purchase_test_create_payments_without_payments(
        nfe_purchase, example_creator, current_station):
    purchase_order = example_creator.create_purchase_order()
    nfe_purchase.purchase_order = purchase_order
    payment = nfe_purchase._create_payments(current_station)

    assert payment.status == Payment.STATUS_PAID
    assert payment.branch is nfe_purchase.purchase_order.branch
    assert payment.station is current_station


def test_nfe_purchase_get_key(nfe_purchase, nfe):
    nfe_purchase.xml = nfe.root

    assert nfe_purchase.get_key() == '53210239681615000166650010000004761226641111'


def test_nfe_purchase_get_key_without_xml(nfe_purchase):
    nfe_purchase.xml = None

    assert nfe_purchase.get_key() is None


def test_nfe_purchase_find_or_create_supplier(nfe_purchase, nfe_supplier):
    nfe_supplier.cnpj = '00.000.000/0000-00'
    supplier = nfe_purchase.find_or_create_supplier(nfe_supplier)
    nfe_supplier.supplier = supplier

    assert supplier is nfe_supplier.supplier


def test_nfe_purchase_find_or_create_supplier_creating_person(store, nfe_purchase):
    person_count = store.find(Person).count()
    nfe_supplier = NFeSupplier(store=store, city_code=1303569, cnpj='00.000.000/0000-00')
    nfe_purchase.find_or_create_supplier(nfe_supplier)

    assert nfe_supplier.supplier.person.company.cnpj is nfe_supplier.cnpj
    assert person_count + 1 == store.find(Person).count()


def test_nfe_purchase_test_create_purchase_order_without_payments(store, nfe_purchase,
                                                                  example_creator, current_station):
    assert nfe_purchase.purchase_order is None
    purchase_order_count = store.find(PurchaseOrder).count()
    payments_count = store.find(Payment).count()
    responsible = example_creator.create_user()
    nfe_purchase.create_purchase_order(responsible, create_payments=False,
                                       station_name=current_station.name)

    assert purchase_order_count + 1 == store.find(PurchaseOrder).count()
    assert payments_count == store.find(Payment).count()


def test_nfe_purchase_test_create_purchase_order_with_payments(store, nfe_purchase,
                                                               example_creator, current_station):
    assert nfe_purchase.purchase_order is None
    purchase_order_count = store.find(PurchaseOrder).count()
    payments_count = store.find(Payment).count()
    NFePayment(store=store, nfe_purchase=nfe_purchase, value=10)
    responsible = example_creator.create_user()
    nfe_purchase.create_purchase_order(responsible, create_payments=True,
                                       station_name=current_station.name)

    assert purchase_order_count + 1 == store.find(PurchaseOrder).count()
    assert payments_count + 1 == store.find(Payment).count()


def test_nfe_purchase_create_receiving_order(store, nfe_purchase, purchase_order,
                                             current_station, nfe_supplier):
    nfe_purchase.purchase_order = purchase_order
    purchase_order.status = PurchaseOrder.ORDER_CONFIRMED
    receiving = nfe_purchase.create_receiving_order(current_station)

    assert set(receiving.purchase_orders) == {purchase_order}


def test_nfe_purchase_create_receiving_order_with_purchase_order_items(
        store, nfe_purchase, purchase_order, current_station, nfe_supplier, sellable,
        example_creator):
    nfe_purchase.purchase_order = purchase_order
    example_creator.create_purchase_order_item(order=purchase_order, sellable=sellable)
    purchase_order.status = PurchaseOrder.ORDER_CONFIRMED
    receiving = nfe_purchase.create_receiving_order(current_station)

    assert set(receiving.purchase_orders) == {purchase_order}


def test_nfe_purchase_create_receiving_order_freight_cif(
        store, nfe_purchase, purchase_order, current_station, nfe_supplier):
    nfe_purchase.purchase_order = purchase_order
    nfe_purchase.freight_type = PurchaseOrder.FREIGHT_CIF
    purchase_order.status = PurchaseOrder.ORDER_CONFIRMED
    receiving = nfe_purchase.create_receiving_order(current_station)

    assert set(receiving.purchase_orders) == {purchase_order}


def test_maybe_create_product_supplier_info_without_info(store, nfe_purchase, nfe_item,
                                                         sellable, example_creator):
    supplier = example_creator.create_supplier()
    nfe_item.sellable = sellable
    nfe_purchase.maybe_create_product_supplier_info(nfe_item, supplier)
    product_supplier_info = store.find(ProductSupplierInfo, supplier=supplier).one()

    assert product_supplier_info.product is nfe_item.sellable.product
    assert product_supplier_info.base_cost == nfe_item.cost


def test_maybe_create_product_supplier_info_with_info(store, nfe_purchase, nfe_item,
                                                      sellable, example_creator):
    supplier = example_creator.create_supplier()
    nfe_item.sellable = sellable
    psi = example_creator.create_product_supplier_info(supplier=supplier,
                                                       product=nfe_item.sellable.product,
                                                       branch=nfe_purchase.branch)
    psi.base_cost = 100
    nfe_purchase.maybe_create_product_supplier_info(nfe_item, supplier)
    product_supplier_info = store.find(ProductSupplierInfo, supplier=supplier).one()

    assert product_supplier_info.product is nfe_item.sellable.product
    assert product_supplier_info.base_cost == nfe_item.cost


def test_nfe_purchase_create_sellable(nfe_purchase, current_branch, current_user, product_info):
    sellable = nfe_purchase.create_sellable(product_info, current_user)

    assert sellable.code == "123"


def test_nfe_purchase_create_sellable_without_code(nfe_purchase, current_branch, current_user,
                                                   product_info):
    product_info['code'] = None
    sellable = nfe_purchase.create_sellable(product_info, current_user)

    assert sellable.barcode == "123"


@pytest.mark.parametrize('sellable_code', ('112', '234', '666'))
def test_nfe_purchase_create_sellable_with_existing_sellable(nfe_purchase, sellable,
                                                             sellable_code, current_user):
    sellable.code = sellable_code
    product_info = {
        "code": sellable.code,
        "is_package": "true",
    }
    assert nfe_purchase.create_sellable(product_info, current_user) is None


def test_nfe_purchase_create_sellable_with_sellable_error(nfe_purchase, product_info, current_user):
    product_info['is_package'] = "false"
    with pytest.raises(SellableError):
        nfe_purchase.create_sellable(product_info, current_user)
