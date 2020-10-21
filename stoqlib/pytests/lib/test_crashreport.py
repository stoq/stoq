import sys
from unittest import mock

from stoqlib.lib.crashreport import collect_traceback


@mock.patch('stoqlib.lib.crashreport.CustomRavenClient')
@mock.patch('stoqlib.lib.crashreport.is_developer_mode')
def test_collect_traceback(is_developer_mode_mock, raven_client_mock):
    is_developer_mode_mock.return_value = False
    try:
        raise ValueError()
    except ValueError:
        tb = sys.exc_info()

    collect_traceback(tb)
