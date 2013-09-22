# -*- coding: utf-8 -*-

# Removal of the products retention functionality.
# Data migration from product retention history table to stock decrease and
# stock decrease item tables.

from stoqlib.database.admin import get_admin_user
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.interfaces import IUser, IEmployee  # pylint: disable=E0611
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product, ProductHistory
from stoqlib.domain.stockdecrease import StockDecrease, StockDecreaseItem
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


def apply_patch(store):
    # Creation of new column in stock_decrease table.
    # And added new Cfop to cfop_data table.
    store.execute("""ALTER TABLE stock_decrease
                   ADD COLUMN cfop_id bigint REFERENCES cfop_data(id);""")

    # Default Cfop should be use in manual stock decrease.
    cfop_data = store.find(CfopData, code=u'5.949').one()
    if not cfop_data:
        cfop_data = CfopData(store=store,
                             code=u"5.949",
                             description=u"Outra saída de mercadoria ou "
                                         u"prestação de serviço não "
                                         u"especificado")

    # Adjusting existing manuals outputs
    for stock_decrease in store.find(StockDecrease):
        stock_decrease.cfop = cfop_data

    retentions = store.execute("""
        SELECT id, quantity, reason, retention_date, product_id, cfop_id
          FROM product_retention_history ORDER BY id;""").get_all()

    # Without retentions, there is no need to create user and employee
    # variables.
    if len(retentions):

        # Default user for migration
        user = get_admin_user(store)
        if user is None:
            users = Person.iselectBy(IUser, is_active=True,
                                     store=store).order_by(Person.id)
            user = users[0]

        # Default employee for migration
        employee = IEmployee(user.person, None)
        if employee is None:
            employees = Person.iselectBy(IEmployee, is_active=True,
                                         store=store).order_by(Person.id)
            employee = employees[0]

        default_branch = sysparam().MAIN_COMPANY
        notes = _(u"Stock decrease imported from old retention.")

    history = store.execute("""
        SELECT id, quantity_retained, sellable_id, branch_id
          FROM product_history
         WHERE quantity_retained is not null
          ORDER BY id;""").get_all()

    for i in range(len(retentions)):
        ret = retentions[i]
        hist = history[i]

        product = Product.get(ret[4], store=store)

        branch_id = hist[3]
        if ret[1] != hist[1] or product.sellable.id != hist[2]:
            branch_id = default_branch.id

        decrease = StockDecrease(store=store,
                                 confirm_date=ret[3],
                                 status=StockDecrease.STATUS_CONFIRMED,
                                 reason=ret[2],
                                 notes=notes,
                                 responsible=user,
                                 removed_by=employee,
                                 branch_id=branch_id,
                                 cfop_id=ret[5])

        decrease_item = StockDecreaseItem(store=store,
                                          quantity=ret[1],
                                          sellable=product.sellable)
        decrease.add_item(decrease_item)
        store.remove(hist[0])
        ProductHistory(branch_id=branch_id, sellable=product.sellable,
                       quantity_decreased=decrease_item.quantity,
                       decreased_date=decrease.confirm_date,
                       store=store)

    store.execute("""ALTER TABLE product_history
                   DROP COLUMN quantity_retained;""")
    store.execute("DROP TABLE product_retention_history;")
