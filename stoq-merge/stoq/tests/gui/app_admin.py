from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'admin'])
app = player.get_app()

player.wait_for_window("AdminApp")
app.AdminApp.search_button.clicked()
app.AdminApp.filter_combo.select_item_by_label("Inactive")
app.AdminApp.filter_combo.select_item_by_label("Active")
app.AdminApp.filter_combo.select_item_by_label("Any")
app.AdminApp.search_entry.set_text("admi")
app.AdminApp.search_entry.activate()
app.AdminApp.search_entry.set_text("")
app.AdminApp.search_entry.activate()
app.AdminApp.users.select_paths(['2'])
app.AdminApp.edit_button.clicked()

player.wait_for_window("UserEditor")
app.UserEditor.cancel_button.clicked()
player.delete_window("UserEditor")

app.AdminApp.change_password_button.clicked()

player.wait_for_window("PasswordEditor")
app.PasswordEditor.cancel_button.clicked()
player.delete_window("PasswordEditor")

app.AdminApp.SalesMenu.activate()
app.AdminApp.Quit.activate()
player.finish()
