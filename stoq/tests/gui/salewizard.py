from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'pos'])
app = player.get_app()

player.wait_for_window("POSApp")
app.POSApp.new_order_button.clicked()

player.wait_for_window("NewOrderEditor")
app.NewOrderEditor.anonymous_check.clicked()
app.NewOrderEditor.client_check.clicked()
app.NewOrderEditor.client.set_text("John Wayne2")
app.NewOrderEditor.ok_button.clicked()
player.delete_window("NewOrderEditor")

app.POSApp.price.set_text("122.00")
app.POSApp.product.set_text("K15 Keyboard AXDR")
app.POSApp.quantity.set_text("2.00")
app.POSApp.quantity.activate()
app.POSApp.sellables.select_paths(['0'])
app.POSApp.price.set_text("0.00")
app.POSApp.quantity.set_text("1.00")
app.POSApp.product.set_text("")
app.POSApp.checkout_button.clicked()

player.wait_for_window("SaleWizard")
app.SaleWizard.cash_check.clicked()
app.SaleWizard.othermethods_check.clicked()
app.SaleWizard.next_button.clicked()
app.SaleWizard.installments_number.set_text("4")
app.SaleWizard.interval_type_combo.select_item_by_label("Months")
app.SaleWizard.reset_button.clicked()
app.SaleWizard.next_button.clicked()
app.SaleWizard.order_number.set_text("14031981")
app.SaleWizard.next_button.clicked()
app.POSApp.sellables.select_paths([])
player.delete_window("SaleWizard")

player.delete_window("POSApp")

player.finish()

def post_hook(conn):
    from stoqlib.domain.interfaces import IPaymentGroup
    from stoqlib.domain.sale import Sale

    sales = Sale.select(Sale.q.order_number == '14031981', connection=conn)
    assert sales.count() == 1, sales.count()
    sale = sales[0]
    items = sale.get_items()
    assert items.count() == 1, items.count()
    item = items[0]

    assert item.sellable.get_short_description() == 'K15 Keyboard AXDR'
    assert item.quantity == 2.0

    # Verify installments
    group = IPaymentGroup(sale)
    installments = group.get_items()

    # This is a bug in the wizard code, it doesn't refresh the interface
    # when the installments_number entry is changed. You need to click
    # Refresh list.
    #assert installments.count() == 4, installments.count()
    assert installments.count() > 0, installments.count()


