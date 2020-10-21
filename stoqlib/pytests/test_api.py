import pytest

from stoqlib.api import api
from stoqlib.database.runtime import get_current_user, get_default_store
from stoqlib.database.settings import db_settings
from stoqlib.l10n.l10n import get_l10n_field
from stoqlib.lib.devicemanager import DeviceManager
from stoqlib.lib.environment import is_developer_mode
from stoqlib.lib.interfaces import IStoqConfig
from stoqlib.lib.settings import get_settings


def test_api():
    store = api.get_default_store()

    assert store is get_default_store()
    assert api.get_current_user(store) is get_current_user(store)
    assert api.db_settings is db_settings
    assert api.user_settings is get_settings()
    assert isinstance(api.device_manager, DeviceManager)
    with pytest.raises(NotImplementedError):
        assert isinstance(api.config, IStoqConfig)
    assert api.is_developer_mode() is is_developer_mode()
    assert api.get_l10n_field('CPF') is get_l10n_field('CPF')
