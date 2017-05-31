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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import contextlib
import hashlib
import os
import platform
import shutil
import subprocess
import tempfile

from OpenSSL import crypto
from stoqlib.domain.certificate import Certificate
from stoqlib.lib.osutils import get_application_dir
from stoqlib.lib.settings import get_settings
from stoqlib.lib.xmlutils import get_signer

_is_windows = platform.system() == 'Windows'
certdb_path = os.path.join(get_application_dir(), 'certdb')
pkcs12_cert_path = os.path.join(certdb_path, 'cert.pfx')
pkcs11_lib_path = os.path.join(certdb_path, 'cert.so')

cert_path = {
    Certificate.TYPE_PKCS11: pkcs11_lib_path,
    Certificate.TYPE_PKCS12: pkcs12_cert_path,
}


def check_certdb():
    """Check if the certdb exists."""
    if not os.path.isdir(certdb_path):
        return False

    # FIXME: There's no nss on Windows
    if _is_windows:
        return True

    return subprocess.call(['modutil', '-dbdir', certdb_path, '-list'],
                           stdout=subprocess.PIPE) == 0


def init_certdb():
    """Initialie the certdb, removing the old one if if exists."""
    if os.path.exists(certdb_path):
        shutil.rmtree(certdb_path)
    os.makedirs(certdb_path)

    # FIXME: There's no nss on Windows
    if _is_windows:
        return

    with tempfile.NamedTemporaryFile(delete=False) as f:
        subprocess.check_call(['certutil', '-N',
                               '-f', f.name, '-d', certdb_path])


def import_pkcs11(content):
    """Import a pkcs11 (A3) certificate.

    :param content: The content of the certificate library
    """
    with open(pkcs11_lib_path, 'wb') as f:
        f.write(content)

    # FIXME: There's no nss on Windows
    if _is_windows:
        return

    subprocess.check_call(['modutil', '-add', 'ca_certs', '-force',
                           '-libfile', pkcs11_lib_path, '-dbdir', certdb_path])


def import_pkcs12(content, password):
    """Import a pkcs12 (A1) certificate.

    :param content: The content of the certificate file
    :param password: The certificate password
    """
    with open(pkcs12_cert_path, 'wb') as f:
        f.write(content)

    # FIXME: There's no nss on Windows
    if _is_windows:
        return

    subprocess.check_call(['pk12util', '-d', certdb_path,
                           '-i', pkcs12_cert_path, '-W', password])


class CertificateManager(object):

    _instance = None

    def __init__(self):
        self.setup_done = False
        self._certificate = None
        self._cert_callback = None
        self._password = None
        self._pw_callback = None
        self._cert_type = None
        self._cert_name = None

    #
    #  Public API
    #

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of this manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def setup_certificate(self, certificate,
                          password_callback=None, certificate_callback=None):
        """Setup the certificate in the manager.

        Setup the certificate and make sure it is ready to be used for
        signing and transmission.

        :param certificate: The :class:`stoqnfe.domain.cert.NfeCertificate`
            that is going to be configured
        :param password_callback: A callable that will be used to ask
            for the certificate password
        :param certificate_callback: A callable that will be used to decide
            which if the existing certificates (PKCS11 only) will be used
        """
        self._cert_name = certificate.name
        self._cert_type = certificate.type
        self._password = certificate.password
        self._pw_callback = password_callback
        self._cert_callback = certificate_callback

        md5sum_file = os.path.join(certdb_path, 'cert.md5sum')
        data = (certificate.content +
                (self._password.hashed_password or b''))
        md5sum = hashlib.md5(data).hexdigest()

        if os.path.isfile(md5sum_file):
            try:
                with open(md5sum_file, 'r') as f:
                    force = md5sum != f.read()
            except Exception:
                force = True
        else:
            force = True

        if not check_certdb() or force:
            init_certdb()
            if certificate.type == Certificate.TYPE_PKCS11:
                import_pkcs11(certificate.content)
            elif certificate.type == Certificate.TYPE_PKCS12:
                import_pkcs12(certificate.content, self._password.password)

            with open(md5sum_file, 'w') as f:
                f.write(md5sum)

        if not _is_windows:
            # FIXME: There's no nss on Windows
            from stoqlib.lib.session import nss_setup
            nss_setup(certdb_path,
                      password_callback=self._password_callback,
                      certificate_callback=self._certificate_callback)

        self.setup_done = True

    @contextlib.contextmanager
    def get_certs(self):
        """Get the certificate and its key in a temporary file.

        This will separate the certificate and the key in temporary files.
        The path to those files will be yielded in the context, and then
        removed from the file system.

        Note that this only works for PKCS12 since there's no way to extract
        the private key from a PKCS11 token.

        :returns: (cert_file_path, key_file_path)
        """
        # This is not supported for PKCS11 yet (and maybe it will never be)
        assert self._cert_type == Certificate.TYPE_PKCS12

        with open(cert_path[self._cert_type], 'rb') as f:
            pkcs12 = crypto.load_pkcs12(f.read(), self._get_password())

        with tempfile.NamedTemporaryFile(delete=False) as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM,
                                                    pkcs12.get_certificate()))
        with tempfile.NamedTemporaryFile(delete=False) as key_file:
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                                  pkcs12.get_privatekey()))

        yield (cert_file.name, key_file.name)

        os.unlink(cert_file.name)
        os.unlink(key_file.name)

    def sign(self, xml):
        """Sign the given xml."""
        backend = get_signer(self._cert_type)
        return backend.get_signature(xml, cert_path[self._cert_type],
                                     self._get_password,
                                     self._certificate_callback)

    #
    #  Private
    #

    def _get_password(self, token_name=None, retry=False):
        # Ask the password in the following conditions:
        # * We are retrying (password was incorrect)
        # * The password was not yet supplied
        password = self._password and self._password.password
        token_name = token_name or self._cert_name

        if retry or password is None:
            self._password = self._pw_callback(token_name, retry)
            password = self._password.password

        return password

    #
    #  Callbacks
    #

    def _password_callback(self, slot, retry, old_password=None):
        return self._get_password(slot.token_name, retry)

    def _certificate_callback(self, certificates):
        if self._certificate is not None and self._certificate in certificates:
            return self._certificate

        # If there's only one certificate, don't need to ask the user
        if len(certificates) == 1:
            self._certificate = certificates[0]
        else:
            settings = get_settings()
            last_used = settings.get('nfe-certificate-last-used', None)
            self._certificate = self._cert_callback(certificates,
                                                    last_used)
            settings.set('nfe-certificate-last-used', self._certificate)

        return self._certificate
