from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'pos'])
app = player.get_app()

player.wait_for_window("POSApp")
app.POSApp.SalesMenu.activate()
app.POSApp.SearchMenu.activate()
app.POSApp.SalesMenu.activate()
app.POSApp.ResetOrder.activate()

player.wait_for_window("NewOrderEditor")
app.NewOrderEditor.cancel_button.clicked()
player.delete_window("POSApp")

player.finish()
