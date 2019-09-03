# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2017 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import errno
import http.client
import logging
import os
import urllib.parse

from nss import io
from nss import nss
from nss import ssl
from nss.error import NSPRError

log = logging.getLogger(__name__)
_certdb = None
_password_callback = None
_certificate_callback = None


def nss_setup(certdb, password_callback=None, certificate_callback=None):
    global _certdb
    global _password_callback
    global _certificate_callback
    _certdb = certdb
    _password_callback = password_callback
    _certificate_callback = certificate_callback


class _NssHTTPConnection(http.client.HTTPConnection):

    default_port = 443

    def __init__(self, host, port, timeout=3, **kwargs):
        http.client.HTTPConnection.__init__(
            self, host, port, timeout=timeout, **kwargs)

        log.info('%s init %s', self.__class__.__name__, host)
        self.sock = None
        self._timeout = timeout
        self._certdb = nss.get_default_certdb()

    def connect(self):
        log.info("connect: host=%s port=%s", self.host, self.port)
        try:
            addr_info = io.AddrInfo(self.host)
        except Exception:
            log.error("could not resolve host address '%s'", self.host)
            raise

        for net_addr in addr_info:
            net_addr.port = self.port
            self._create_socket(net_addr.family)
            try:
                log.info("try connect: %s", net_addr)
                self.sock.connect(net_addr,
                                  timeout=io.seconds_to_interval(self._timeout))
            except Exception as e:
                log.info("connect failed: %s (%s)", net_addr, e)
            else:
                log.info("connected to: %s", net_addr)
                break
        else:
            raise IOError(errno.ENOTCONN,
                          "Could not connect to %s at port %d" % (self.host, self.port))

    def _create_socket(self, family):
        self.sock = ssl.SSLSocket(family)
        self.sock.set_ssl_option(ssl.SSL_SECURITY, True)
        self.sock.set_ssl_option(ssl.SSL_HANDSHAKE_AS_CLIENT, True)
        self.sock.set_hostname(self.host)

        # Provide a callback to verify the servers certificate
        self.sock.set_auth_certificate_callback(
            self._auth_certificate_callback, self._certdb)
        self.sock.set_client_auth_data_callback(
            self._client_auth_data_callback, '', '', self._certdb)

    def _auth_certificate_callback(self, sock, check_sig, is_server, certdb):
        cert = sock.get_peer_certificate()
        intended_usage = nss.certificateUsageSSLServer
        try:
            # If the cert fails validation it will raise an exception, the errno attribute
            # will be set to the error code matching the reason why the validation failed
            # and the strerror attribute will contain a string describing the reason.

            # XXX: After python3 migration, this is not working properly. Assume that
            # the intented usage is valid for now.
            #pin_args = sock.get_pkcs11_pin_arg() or ()
            #approved_usage = cert.verify_now(certdb, check_sig, intended_usage, *pin_args)
            approved_usage = intended_usage
        except Exception as e:
            # XXX: Why isn't the certificate valid?
            logging.info('cert validation failed for "%s" (%s)', cert.subject, e.strerror)
            approved_usage = intended_usage

        logging.debug("approved_usage = %s intended_usage = %s",
                      ', '.join(nss.cert_usage_flags(approved_usage)),
                      ', '.join(nss.cert_usage_flags(intended_usage)))

        if not bool(approved_usage & intended_usage):
            logging.debug('cert not valid for "%s"', cert.subject)
            return False

        # Certificate is OK.  Since this is the client side of an SSL
        # connection, we need to verify that the name field in the cert
        # matches the desired hostname.  This is our defense against
        # man-in-the-middle attacks.
        hostname = sock.get_hostname()
        try:
            # If the cert fails validation it will raise an exception
            cert_is_valid = cert.verify_hostname(hostname)
        except Exception as e:
            logging.error('failed verifying socket hostname "%s" matches cert subject "%s" (%s)',
                          hostname, cert.subject, e.strerror)
            return False

        logging.debug('cert valid %s for "%s"', cert_is_valid, cert.subject)
        return cert_is_valid

    def _client_auth_data_callback(self, ca_names, chosen_nickname, password, nicknames):
        nickname = _certificate_callback(
            nss.get_cert_nicknames(self._certdb, nss.SEC_CERT_NICKNAMES_USER))
        try:
            cert = nss.find_cert_from_nickname(nickname, password)
            priv_key = nss.find_key_by_any_cert(cert, password)
        except NSPRError:
            return False

        return cert, priv_key


class NssResponse(object):
    """Nss response object.

    This maps the nss response os a request to the same API that requests
    used, making it easier to exchange one for another
    """

    def __init__(self, response):
        self._response = response
        self.status_code = response.status
        self.reason = response.reason

    @property
    def content(self):
        return self._response.read()


class NssSession(object):
    """Nss session to communicate with Sefaz using a certificate.

    When using this, make sure to :meth:`.init` it and :meth:`.shutdown`
    after. This is specially important for A3 certificates so it can
    free the token for the signature code to work. The easies way
    for doing that is by using a contextmanager like::

      >> with NssSession() as s:
      ..    s.post('some_url')

    """

    SCHEME_PORT_MAP = {
        'http': 80,
        'https': 443,
    }

    def __init__(self):
        # Reuse socks as much as we can. This dict will map
        # the netloc:port to an open _NssHTTPConnection to that location
        self._conns = {}

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, *args):
        for conn in self._conns.values():
            conn.close()
        self.shutdown()

    def init(self):
        if nss.nss_is_initialized():
            return

        if _password_callback is not None:
            nss.set_password_callback(_password_callback)

        nss.nss_init(_certdb)
        ssl.set_domestic_policy()

    def shutdown(self):
        if not nss.nss_is_initialized():
            return

        try:
            ssl.clear_session_cache()
        except Exception:
            pass
        try:
            nss.nss_shutdown()
        except Exception:
            pass

    def get(self, url, headers=None):
        return self.request('GET', url, headers=headers)

    def post(self, url, data=None, headers=None, timeout=None):
        return self.request('POST', url, data=data, headers=headers,
                            timeout=timeout)

    def request(self, method, url, data=None, headers=None, timeout=None):
        parsed = urllib.parse.urlparse(url)
        port = parsed.port
        if not port:
            port = self.SCHEME_PORT_MAP[parsed.scheme]

        key = (parsed.netloc, port)
        conn = self._conns.get(key, None)
        if conn is None:
            conn = self._conns.setdefault(key, _NssHTTPConnection(parsed.netloc,
                                                                  port,
                                                                  timeout=timeout))
            conn.connect()

        # FIXME: python-nss stores password_callback on a per-thread dict
        # Since this object will be called from different threads,
        # some would not find it. It is not a big problem since setting the
        # password callback is a fast operation, but maybe there's
        # some better solution here?
        if _password_callback is not None:
            nss.set_password_callback(_password_callback)

        conn.request(method, parsed.path, body=data, headers=headers)
        return NssResponse(conn.getresponse())


if __name__ == '__main__':
    firefoxdir = os.path.join(os.environ['HOME'], '.mozilla', 'firefox')
    if not os.path.exists(firefoxdir):
        raise AssertionError

    import configparser
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(firefoxdir, 'profiles.ini'))
    nss_setup(os.path.join(firefoxdir, cfg.get('Profile0', 'Path')))

    url = 'https://nfce-homologacao.sefazrs.rs.gov.br/ws/NfeStatusServico/NFeStatusServico2.asmx'
    data = ('<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
            'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<soap:Header>'
            '<nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NfeStatusServico2">'
            '<versaoDados>3.10</versaoDados><cUF>43</cUF></nfeCabecMsg></soap:Header>'
            '<soap:Body>'
            '<nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NfeStatusServico2">'
            '<consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="3.10">'
            '<tpAmb>2</tpAmb><cUF>43</cUF><xServ>STATUS</xServ></consStatServ>'
            '</nfeDadosMsg></soap:Body></soap:Envelope>')
    headers = {'Content-type': u'application/soap+xml; charset=utf-8',
               'Accept': u'application/soap+xml; charset=utf-8'}
    with NssSession() as s:
        res = s.post(url, data, headers)
        print("status:", res.status_code)
        print("reason:", res.reason)
        print("text:", res.text)
