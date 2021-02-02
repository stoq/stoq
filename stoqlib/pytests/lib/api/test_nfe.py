from decimal import Decimal

import pytest
from kiwi.currency import currency
from lxml import etree

from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.lib.api.nfe import NFe
from stoqlib.lib.unittestutils import get_pytests_dir


@pytest.fixture
def nfe(store):
    nfe_xml_path = get_pytests_dir('lib/api/data/') + 'nfe.xml'
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(nfe_xml_path, parser)
    nfe_file = etree.tostring(tree).decode('utf-8')

    nfe = NFe(file_handler=nfe_file, store=store)
    return nfe


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
