import pytest

from stoqlib.domain.nfe import NFeItem, NFeSupplier, NFePurchase


@pytest.fixture
def sellable(example_creator):
    return example_creator.create_sellable()


@pytest.fixture
def nfe_supplier(store):
    return NFeSupplier(store=store)


@pytest.fixture
def nfe_item(store, nfe_purchase):
    return NFeItem(store=store, nfe_purchase=nfe_purchase)


@pytest.fixture
def nfe_purchase(store, current_branch):
    return NFePurchase(store=store, branch=current_branch)


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
