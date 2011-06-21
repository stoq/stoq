# -*- coding: utf-8 -*-

# Removal of the products retention functionality.
# Data migration from product retention history table to stock decrease and
# stock decrease item tables.

from stoqlib.database.admin import get_admin_user
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.interfaces import IUser, IEmployee
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

def apply_patch(trans):
    #Creation of new column in stock_decrease table.
    #And added new Cfop to cfop_data table.
    trans.query("""ALTER TABLE stock_decrease
                   ADD COLUMN cfop_id bigint REFERENCES cfop_data(id);""")

    # Default Cfop should be use in manual stock decrease.
    cfop_data = CfopData.selectOneBy(code='5.949', connection=trans)
    if not cfop_data:
        cfop_data = CfopData(connection=trans,
                             code="5.949",
                             description=u"Outra saída de mercadoria ou "
                                         u"prestação de serviço não "
                                         u"especificado")

    # Adjusting existing manuals outputs
    for stock_decrease in StockDecrease.select(connection=trans):
        stock_decrease.cfop = cfop_data

    retentions = trans.queryAll("""
        SELECT id, quantity, reason, retention_date, product_id, cfop_id
          FROM product_retention_history ORDER BY id;""")

    # Without retentions, there is no need to create user and employee
    # variables.
    if len(retentions):

        # Default user for migration
        user = get_admin_user(trans)
        if user is None:
            users = Person.iselectBy(IUser, is_active=True,
                                     connection=trans).orderBy('id')
            user = users[0]

        # Default employee for migration
        employee = IEmployee(user.person, None)
        if employee is None:
            employees = Person.iselectBy(IEmployee, is_active=True,
                                         connection=True).orderBy('id')
            employee = employees[0]

        default_branch = sysparam(trans).MAIN_COMPANY
        notes = _(u"Stock decrease imported from old retention.")

    history = trans.queryAll("""
        SELECT id, quantity_retained, sellable_id, branch_id
          FROM product_history
         WHERE quantity_retained is not null
          ORDER BY id;""")

    for i in range(len(retentions)):
        ret = retentions[i]
        hist = history[i]

        product = Product.get(ret[4], connection=trans)

        branch_id = hist[3]
        if ret[1] != hist[1] or product.sellable.id != hist[2]:
            branch_id = default_branch.id

        decrease = StockDecrease(connection=trans,
                                 confirm_date=ret[3],
                                 status=StockDecrease.STATUS_CONFIRMED,
                                 reason=ret[2],
                                 notes=notes,
                                 responsible=user,
                                 removed_by=employee,
                                 branchID=branch_id,
                                 cfopID=ret[5])

        decrease_item = StockDecreaseItem(connection=trans,
                                          quantity=ret[1],
                                          sellable=product.sellable)
        decrease.add_item(decrease_item)

        ProductHistory.delete(hist[0], trans)
        ProductHistory(branchID=branch_id, sellable=product.sellable,
                       quantity_decreased=decrease_item.quantity,
                       decreased_date=decrease.confirm_date,
                       connection=trans)


    trans.query("""ALTER TABLE product_history
                   DROP COLUMN quantity_retained;""")
    trans.query("DROP TABLE product_retention_history;")
