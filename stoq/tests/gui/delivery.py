from kiwi.ui.test.player import Player

player = Player(['bin/stoq', 'pos'])
app = player.get_app()

player.wait_for_window("POSApp")
app.POSApp.SearchMenu.activate()
app.POSApp.Clients.activate()

player.wait_for_window("ClientSearch")
app.ClientSearch.search_button.clicked()
app.ClientSearch.ObjectList.select_paths(['0'])
app.ClientSearch.ObjectList.select_paths(['2'])
app.ClientSearch.edit_button.clicked()

player.wait_for_window("ClientEditor")
app.ClientEditor.contacts_button.clicked()

player.wait_for_window("LiaisonListDialog")
app.LiaisonListDialog.add_button.clicked()

player.wait_for_window("ContactEditor")
app.ContactEditor.cancel_button.clicked()
app.LiaisonListDialog.cancel_button.clicked()
app.ClientEditor.ok_button.clicked()
player.delete_window("ClientSearch")

player.delete_window("POSApp")

player.finish()
