from stoqlib.domain.person import Company, Individual, Person


def test_get_accountants_with_one_accountant(example_creator):
    branch = example_creator.create_branch()
    accountant_role = example_creator.create_employee_role('Contador')
    accountant = example_creator.create_employee(role=accountant_role)
    accountant.branch = branch

    assert set(branch.get_accountants()) == {accountant}


def test_get_accountants_with_two_accountants(example_creator):
    branch = example_creator.create_branch()
    accountant_role = example_creator.create_employee_role('Contador')

    accountant1 = example_creator.create_employee(role=accountant_role)
    accountant2 = example_creator.create_employee(role=accountant_role)

    accountant1.branch = branch
    accountant2.branch = branch

    assert set(branch.get_accountants()) == {accountant1, accountant2}


def test_get_accountants_without_accountant(example_creator):
    branch = example_creator.create_branch()
    employee = example_creator.create_employee()
    employee.branch = branch

    assert not branch.get_accountants()


def test_get_accountants_without_branch_specified(example_creator):
    branch = example_creator.create_branch()
    accountant_role = example_creator.create_employee_role('Contador')
    accountant = example_creator.create_employee(role=accountant_role)
    accountant.branch = None

    assert not branch.get_accountants()


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
