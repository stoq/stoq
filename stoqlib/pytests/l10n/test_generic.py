from stoqlib.l10n.generic import generic


def test_company_document():
    assert generic.company_document.validate("") is True


def test_person_document():
    assert generic.person_document.validate("") is True


def test_state():
    assert generic.state.validate("") is True


def test_city():
    assert generic.city.validate("Rolândia", state="PR", country="Brazil") is True
