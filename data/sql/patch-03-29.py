from stoqlib.domain.person import UserBranchAccess
from stoqlib.lib.parameters import sysparam


def apply_patch(trans):
    new_table_query = """
    CREATE TABLE user_branch_access(
        id serial NOT NULL PRIMARY KEY,
        te_created_id bigint UNIQUE REFERENCES transaction_entry(id),
        te_modified_id bigint UNIQUE REFERENCES transaction_entry(id),
        user_id bigint NOT NULL REFERENCES login_user(id) ON UPDATE CASCADE,
        branch_id bigint NOT NULL REFERENCES branch(id) ON UPDATE CASCADE,
        UNIQUE(user_id, branch_id)
    );"""
    trans.execute(new_table_query)

    new_column_query = """
    ALTER TABLE employee ADD COLUMN branch_id bigint REFERENCES branch(id)
        ON UPDATE CASCADE;
    """
    trans.execute(new_column_query)

    main_company = sysparam(trans).MAIN_COMPANY
    if main_company:
        update_employee = ("""UPDATE employee SET branch_id = %s""") % main_company.id
        trans.execute(update_employee)

    query = """
    SELECT branch.id as branch_id, login_user.id as user_id
    FROM branch, login_user
    WHERE branch.is_active = true AND login_user.is_active = true
    """
    accesses = trans.execute(query).get_all()
    for (branch_id, user_id) in accesses:
        UserBranchAccess(store=trans, user=user_id, branch=branch_id)
