from stoqlib.l10n.br import br


def test_company_document():
    assert br.company_document.validate("") is False


def test_person_document():
    assert br.person_document.validate("") is False


def test_state():
    assert br.state.validate("") is False
    assert br.state.validate("SP") is True


def test_city():
    assert br.city.validate("") is False
    assert br.city.validate("Rolândia", state="PR", country="Brazil") is True
