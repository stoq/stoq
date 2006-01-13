from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'pos'])
app = player.get_app()

player.wait_for_window("POSApp")
app.POSApp.new_order_button.clicked()

player.wait_for_window("BasicWrappingDialog")
app.BasicWrappingDialog.anonymous_check.clicked()
app.BasicWrappingDialog.client_check.clicked()
app.BasicWrappingDialog.client.set_text("John Wayne2")
app.BasicWrappingDialog.ok_button.clicked()
player.delete_window("BasicWrappingDialog")

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
