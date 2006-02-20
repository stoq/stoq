from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'pos'])
app = player.get_app()

player.wait_for_window("POSApp")
app.POSApp.new_order_button.clicked()

player.wait_for_window("NewOrderEditor")
app.NewOrderEditor.anonymous_check.clicked()
app.NewOrderEditor.client_check.clicked()
app.NewOrderEditor.client.set_text("a")
app.NewOrderEditor.client.set_text("")
app.NewOrderEditor.client.set_text("John Wayne")
app.NewOrderEditor.ok_button.clicked()
player.delete_window("NewOrderEditor")

app.POSApp.product.set_text("a")
app.POSApp.product.set_text("")
app.POSApp.product.set_text("K15 Keyboard AXDR")
app.POSApp.quantity.set_text("")
app.POSApp.quantity.set_text("2.00")
app.POSApp.quantity.set_text("")
app.POSApp.quantity.set_text("3.00")
app.POSApp.add_button.clicked()
app.POSApp.sellables.select_paths(['0'])
app.POSApp.quantity.set_text("")
app.POSApp.quantity.set_text("1.00")
app.POSApp.product.set_text("")
app.POSApp.product.set_text("")
app.POSApp.checkout_button.clicked()

player.wait_for_window("SaleWizard")
app.SaleWizard.cancel_button.clicked()
player.delete_window("SaleWizard")

player.delete_window("POSApp")

player.finish()
