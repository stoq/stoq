import base64
import os

from kiwi.utils import gsignal
from twisted.internet import defer, reactor
from twisted.web.xmlrpc import Proxy

from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.process import Process


def _get_random_id():
    return base64.urlsafe_b64encode(os.urandom(8))[:-1]


class DaemonManager(gobject):
    def __init__(self):
        self._daemon_id = _get_random_id()
        self._port = None

    def start(self):
        self.process = Process([
            'stoq-daemon', '--daemon-id', self._daemon_id])

        reactor.callLater(0.1, self._check_active)
        self._defer = defer.Deferred()
        return self._defer

    def _check_active(self):
        appdir = get_application_dir()
        portfile = os.path.join(appdir, 'daemon', self._daemon_id, 'port')

        data = open(portfile).read()
        self._port = int(data)
        self._defer.callback(self)

    def get_client(self):
        return Proxy('http://localhost:%d/XMLRPC' % (self._port, ))


def start_daemon():
    d = DaemonManager()
    return d.start()
