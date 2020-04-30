from stoqlib.domain.person import Company, Individual, Person


def test_get_or_create_by_document_with_existing_person(store, example_creator):
    person = example_creator.create_person()
    individual = example_creator.create_individual(person=person)
    individual.cpf = '437.433.508-07'

    assert Person.get_or_create_by_document(store, '437.433.508-07') is person


def test_get_or_create_by_document_with_cpf(store):
    assert store.find(Individual, cpf='123.456.789-10').count() == 0

    person = Person.get_or_create_by_document(store, '123.456.789-10')

    individual = store.find(Individual, cpf='123.456.789-10').one()
    assert individual is not None
    assert person is not None


def test_get_or_create_by_document_with_cnpj(store):
    assert store.find(Company, cnpj='71.255.183/0001-34').count() == 0

    person = Person.get_or_create_by_document(store, '71.255.183/0001-34')

    company = store.find(Company, cnpj='71.255.183/0001-34').one()
    assert company is not None
    assert person is not None
