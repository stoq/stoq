import pytest
from unittest import mock

from stoqlib.domain.sellable import Sellable


@pytest.fixture
def sellable(example_creator):
    return example_creator.create_sellable()


@pytest.fixture
def override(example_creator, sellable):
    return example_creator.create_sellable_branch_override(sellable=sellable)


def test_get_from_override_with_boolean_attr(example_creator, override):
    override.sellable.requires_kitchen_production = True
    override.requires_kitchen_production = False

    rv = override.sellable._get_from_override('requires_kitchen_production', override.branch)
    assert rv is False


def test_get_from_override_with_override_none(sellable, current_branch):
    sellable.description = 'test'

    assert sellable._get_from_override('description', current_branch) == 'test'


def test_get_from_override_with_attr_none(example_creator, override):
    override.sellable.base_price = 10
    override.base_price = None

    assert override.sellable._get_from_override('base_price', override.branch) == 10


def test_get_from_override_with_attr_typo(sellable, current_branch):
    with pytest.raises(AttributeError):
        sellable._get_from_override('fake_attr', current_branch)


def test_get_from_override(example_creator, override):
    override.sellable.base_price = 10
    override.base_price = 20

    assert override.sellable._get_from_override('base_price', override.branch) == 20


@mock.patch('stoqlib.domain.sellable.Sellable._get_from_override')
@mock.patch('stoqlib.domain.sellable.sysparam.compare_object', return_value=True)
def test_is_available_with_delivery_service(
    mock_compare_object, mock_get_from_override, sellable,
    current_branch
):

    available = sellable.is_available(current_branch)

    assert mock_get_from_override.call_count == 0
    assert available is True


@pytest.mark.parametrize(
    'status, rv', [(Sellable.STATUS_AVAILABLE, True), (Sellable.STATUS_CLOSED, False)]
)
def test_is_available(status, rv, sellable, current_branch):
    sellable.status = status
    assert sellable.is_available(current_branch) is rv


@pytest.mark.parametrize(
    'status, rv', [(Sellable.STATUS_CLOSED, True), (Sellable.STATUS_AVAILABLE, False)]
)
def test_is_closed(status, rv, sellable, current_branch):
    sellable.status = status
    assert sellable.is_closed(current_branch) is rv
