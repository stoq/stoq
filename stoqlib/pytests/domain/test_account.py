from stoqlib.domain.account import Account


def test_account_get_accounts(store, example_creator):
    account = example_creator.create_account()

    accounts = list(Account.get_accounts(store))
    assert account in accounts
    assert accounts == list(store.find(Account))
