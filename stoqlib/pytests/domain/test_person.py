from stoqlib.domain.person import Branch, CallsView, Company, Individual, Person


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


def test_company_find_by_cnpj_without_branch(store, example_creator):
    company = example_creator.create_company()
    company.cnpj = '71.225.183/0001-34'
    branch = Branch.find_by_cnpj(store, company.cnpj)
    assert branch.is_empty()


def test_company_find_by_cnpj_not_found(store, example_creator):
    branch = example_creator.create_branch()
    # company.cnpj = '71.225.183/0001-34'
    branch = Branch.find_by_cnpj(store, '71.225.183/0001-34')
    assert branch.is_empty()


def test_company_find_by_cnpj(store, example_creator):
    branch = example_creator.create_branch(cnpj='71.225.183/0001-34')
    branch2 = example_creator.create_branch(cnpj='71.225.183/0001-34')
    branches = Branch.find_by_cnpj(store, '71.225.183/0001-34')
    assert set(branches) == {branch, branch2}


def test_company_find_by_cnpj_with_extra_query(store, example_creator):
    branch = example_creator.create_branch(cnpj='71.225.183/0001-34')
    branch.name = 'teste'
    branch2 = example_creator.create_branch(cnpj='71.225.183/0001-34')
    branch2.name = 'should not be found'
    extra_query = Branch.name == 'teste'
    branches = Branch.find_by_cnpj(store, '71.225.183/0001-34', extra_query=extra_query)
    assert set(branches) == {branch}


def test_get_or_create_by_document_with_existing_person(store, example_creator):
    person = example_creator.create_person()
    individual = example_creator.create_individual(person=person)
    individual.cpf = '437.433.508-07'

    assert Person.get_or_create_by_document(store, '437.433.508-07') is person


def test_get_or_create_by_document_with_cpf(store):
    assert store.find(Individual, cpf='123.456.789-10').count() == 0

    person = Person.get_or_create_by_document(store, '123.456.789-10')

    individual = store.find(Individual, cpf='123.456.789-10').one()

    assert individual.person == person
    assert individual.cpf == '123.456.789-10'


def test_get_or_create_by_document_with_cnpj(store):
    assert store.find(Company, cnpj='71.255.183/0001-34').count() == 0

    person = Person.get_or_create_by_document(store, '71.255.183/0001-34')

    company = store.find(Company, cnpj='71.255.183/0001-34').one()

    assert company.person == person
    assert company.cnpj == '71.255.183/0001-34'


def test_company_get_distinct_cnpj_from_branch_without_branch(store, example_creator):
    companies = Company.get_distinct_cnpj_from_branch(store)
    # there is already 2 companies created before the test
    assert len(set(companies)) == 2
    company = example_creator.create_company()
    company.cnpj = '71.225.183/0001-34'

    companies = Company.get_distinct_cnpj_from_branch(store)

    assert len(set(companies)) == 2


def test_company_get_distinct_cnpj_from_branch(store, example_creator):
    companies = Company.get_distinct_cnpj_from_branch(store)
    # there is already 2 companies created before the test
    assert len(set(companies)) == 2
    example_creator.create_branch(cnpj='71.225.183/0001-34')

    companies = Company.get_distinct_cnpj_from_branch(store)

    assert len(set(companies)) == 3


def test_company_get_distinct_cnpj_from_branch_with_duplicated_cnpj(store, example_creator):
    companies = Company.get_distinct_cnpj_from_branch(store)
    # there is already 2 companies created before the test
    assert len(set(companies)) == 2
    example_creator.create_branch(cnpj='71.225.183/0001-34')
    example_creator.create_branch(cnpj='71.225.183/0001-34')

    companies = Company.get_distinct_cnpj_from_branch(store)

    assert len(set(companies)) == 3


def test_person_get_items(store, current_branch):
    assert Person.get_items(store, Person.branch == current_branch)


def test_client_get_client_products(example_creator):
    client = example_creator.create_client()

    products = client.get_client_products(with_children=False)
    assert len(list(products)) == 0


def test_calls_view_find_by_client_date(store):
    calls = CallsView.find_by_client_date(store, None, None)

    assert list(calls) == list(store.find(CallsView))
