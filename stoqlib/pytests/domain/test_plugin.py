from stoqlib.domain.plugin import InstalledPlugin


def test_plugin_get_pre_plugin_nammes(store):
    assert InstalledPlugin.get_pre_plugin_names(store) == []

    InstalledPlugin(store=store, plugin_name="teste")
    assert InstalledPlugin.get_pre_plugin_names(store) == ["teste"]
