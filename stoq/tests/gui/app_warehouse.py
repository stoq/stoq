from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'warehouse'])
app = player.get_app()

player.wait_for_window("WarehouseApp")
app.WarehouseApp.search_button.clicked()
app.WarehouseApp.filter_combo.select_item_by_label("Mad dog")
app.WarehouseApp.filter_combo.select_item_by_label("The dude")
app.WarehouseApp.filter_combo.select_item_by_label("Mickey Mouse")
app.WarehouseApp.filter_combo.select_item_by_label("John Wayne")
app.WarehouseApp.filter_combo.select_item_by_label("Async Open Source")
app.WarehouseApp.SalesMenu.activate()
app.WarehouseApp.Quit.activate()
player.finish()
