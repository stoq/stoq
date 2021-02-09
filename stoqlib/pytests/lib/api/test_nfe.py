from decimal import Decimal

from kiwi.currency import currency

from stoqlib.domain.purchase import PurchaseOrder


def test_nfe_process(nfe, example_creator):
    branch = example_creator.create_branch(cnpj='95.941.054/0001-68')
    nfe_purchase = nfe.process()

    assert nfe_purchase.branch == branch
    assert nfe_purchase.cnpj == '95.941.054/0001-68'
    assert nfe_purchase.freight_cost == currency(Decimal('0'))
    assert nfe_purchase.freight_type == PurchaseOrder.FREIGHT_FOB
    assert nfe_purchase.invoice_number == 476
    assert nfe_purchase.invoice_series == 1
    assert nfe_purchase.total_cost == currency(Decimal('31.18'))
