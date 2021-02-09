import pytest
from lxml import etree

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
