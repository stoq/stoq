from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'purchase'])
app = player.get_app()

player.wait_for_window("PurchaseApp")
app.PurchaseApp.search_button.clicked()
app.PurchaseApp.filter_combo.select_item_by_label("Closed")
app.PurchaseApp.filter_combo.select_item_by_label("Confirmed")
app.PurchaseApp.filter_combo.select_item_by_label("Pending")
app.PurchaseApp.filter_combo.select_item_by_label("Quoting")
app.PurchaseApp.filter_combo.select_item_by_label("Cancelled")
app.PurchaseApp.filter_combo.select_item_by_label("Any")
app.PurchaseApp.search_button.clicked()
app.PurchaseApp.orders.select_paths([(1, )])
app.PurchaseApp.details_button.clicked()

player.wait_for_window("PurchaseDetailsDialog")
player.delete_window("PurchaseDetailsDialog")

app.PurchaseApp.anytime_check.clicked()
app.PurchaseApp.date_check.clicked()
app.PurchaseApp.start_date.set_text("02/25/2006")
app.PurchaseApp.end_date.set_text("02/25/2006")
app.PurchaseApp.search_button.clicked()
app.PurchaseApp.orders.select_paths([])
app.PurchaseApp.PurchaseMenu.activate()
app.PurchaseApp.Quit.activate()
player.finish()
