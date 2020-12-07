import pytest


@pytest.fixture
def sale(example_creator):
    return example_creator.create_sale()


@pytest.fixture
def sale_item(example_creator):
    return example_creator.create_sale_item()


@pytest.fixture
def sellable(example_creator):
    return example_creator.create_sellable()


def test_sale_invoice_subtotal(sale):
    assert sale.invoice_subtotal == sale.get_sale_subtotal()


def test_sale_invoice_total(sale):
    assert sale.invoice_total == sale.get_total_sale_amount()


def test_sale_get_returned_value(sale):
    assert sale.get_returned_value() == 0


def test_sale_has_pre_created_sellables(example_creator, sale, sellable):
    sellable.notes = sellable.NOTES_CREATED_VIA_SALE
    example_creator.create_sale_item(sale=sale, sellable=sellable)

    assert sale.has_pre_created_sellables


def test_sale_does_not_have_pre_created_sellables(example_creator, sale):
    example_creator.create_sale_item(sale=sale)

    assert not sale.has_pre_created_sellables


def test_reset_taxes(example_creator, sale_item):
    product_cofins_template = example_creator.create_product_cofins_template(p_cofins=1)
    sale_item.sellable.product.cofins_template_id = product_cofins_template.id

    product_icms_template = example_creator.create_product_icms_template(p_icms=18)
    sale_item.sellable.product.icms_template_id = product_icms_template.id

    product_ipi_template = example_creator.create_product_ipi_template(p_ipi=2)
    sale_item.sellable.product.ipi_template_id = product_ipi_template.id

    product_pis_template = example_creator.create_product_pis_template(p_pis=1)
    sale_item.sellable.product.pis_template_id = product_pis_template.id

    sbo = example_creator.create_sellable_branch_override(
        sellable=sale_item.sellable, branch=sale_item.sale.branch)
    cfop_data = example_creator.create_cfop_data()
    sbo.default_sale_cfop_id = cfop_data.id

    assert sale_item.cofins_info.p_cofins is None
    assert sale_item.icms_info.p_icms is None
    assert sale_item.ipi_info.p_ipi is None
    assert sale_item.pis_info.p_pis is None
    assert sale_item.cfop_id != sbo.default_sale_cfop_id

    sale_item.sale.reset_taxes()

    assert sale_item.cofins_info.p_cofins == 1
    assert sale_item.icms_info.p_icms == 18
    assert sale_item.ipi_info.p_ipi == 2
    assert sale_item.pis_info.p_pis == 1
    assert sale_item.cfop_id == sbo.default_sale_cfop_id


def test_reset_taxes_already_with_templates(example_creator, sale_item):
    sale_item.cofins_info.p_cofins = 1
    sale_item.cofins_info.p_icms = 1
    sale_item.cofins_info.p_ipi = 1
    sale_item.cofins_info.p_pis = 1

    product_cofins_template = example_creator.create_product_cofins_template(p_cofins=2)
    sale_item.sellable.product.cofins_template_id = product_cofins_template.id

    product_icms_template = example_creator.create_product_icms_template(p_icms=2)
    sale_item.sellable.product.icms_template_id = product_icms_template.id

    product_ipi_template = example_creator.create_product_ipi_template(p_ipi=2)
    sale_item.sellable.product.ipi_template_id = product_ipi_template.id

    product_pis_template = example_creator.create_product_pis_template(p_pis=2)
    sale_item.sellable.product.pis_template_id = product_pis_template.id

    sale_item.sale.reset_taxes()

    assert sale_item.cofins_info.p_cofins == 2
    assert sale_item.icms_info.p_icms == 2
    assert sale_item.ipi_info.p_ipi == 2
    assert sale_item.pis_info.p_pis == 2


def test_reset_taxes_without_sbo(example_creator, sale_item):
    initial_cfop_id = sale_item.cfop_id
    sale_item.sale.reset_taxes()

    assert sale_item.cfop_id == initial_cfop_id


def test_reset_taxes_sbo_without_default_sale_cfop_id(example_creator, sale_item):
    initial_cfop_id = sale_item.cfop_id
    example_creator.create_sellable_branch_override(sellable=sale_item.sellable,
                                                    branch=sale_item.sale.branch)
    sale_item.sale.reset_taxes()

    assert sale_item.cfop_id == initial_cfop_id
