from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'sales'])
app = player.get_app()

player.wait_for_window("SalesApp")
app.SalesApp.search_button.clicked()
app.SalesApp.filter_combo.select_item_by_label("Closed")
app.SalesApp.filter_combo.select_item_by_label("Cancelled")
app.SalesApp.filter_combo.select_item_by_label("Any")
app.SalesApp.filter_combo.select_item_by_label("Opened")
app.SalesApp.TillMenu.activate()
app.SalesApp.quit_action.activate()
player.finish()
