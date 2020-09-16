# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015-2017 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>

import base64
import copy
from decimal import Decimal
import hashlib
import logging
import os.path
import re
import subprocess
import tempfile
from xml.sax.saxutils import escape

from dateutil.tz import tzlocal
from lxml import etree
from OpenSSL import crypto
from stoqlib.lib.stringutils import strip_accents

from stoqlib.domain.certificate import Certificate
from stoqlib.lib.translation import stoqlib_gettext as _


try:
    import PyKCS11
except ImportError:
    pass

try:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    from cryptography.hazmat.primitives.hashes import SHA1
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
    has_cryptography = True
except ImportError:
    has_cryptography = False


log = logging.getLogger(__name__)


class XmlValidationException(Exception):
    pass


class BaseTag(etree.ElementBase):
    # FIXME: How are we going to handle tags with namespaces? Note that we cannot define
    # NAMESPACE = None, otherwise lxml would add an empty namespace here.
    #NAMESPACE = None

    def setup(self):
        """Setup hook for this tag.

        Subclasses can override this if they need to create children nodes, but
        they always need to return self.
        """
        return self

    def append_tag(self, tag, value, mandatory=True, cdata=False):
        if value in [None, ''] and not mandatory:
            # If the tag is not mandatory and the value is empty,
            # dont add the tag to the xml.
            return

        if cdata and value is not None:
            value = etree.CDATA(str(value))
        elif value is not None:
            value = escape(strip_accents(str(value).strip()))

        if hasattr(self, 'NAMESPACE'):
            tag = etree.SubElement(self, '{%s}%s' % (self.NAMESPACE, tag))
        else:
            tag = etree.SubElement(self, tag)

        tag.text = value

    def export(self, filename, idented=False):
        with open(filename, 'wb') as fp:
            fp.write(etree.tostring(self, pretty_print=idented))

    def validate(self, xsd_file):
        """Validates this xml against the given xsd filename.

        :raises: :exc:`XmlValidationException` if the xml is not valid
        """
        xsd = etree.XMLSchema(file=xsd_file)
        xsd.validate(self)
        errors_log = xsd.error_log

        if errors_log:
            log.warning("XML with errors")
        else:
            log.debug("XML validated")
            return

        fields = set()
        for error in xsd.error_log:
            msg = error.message
            log.error("{}: {} {} {}".format(
                error.level_name, error.line, error.column, msg))

            # Remove some useless info from the message. Maybe we should just
            # get the field name from the message and display it?
            match = re.search("'{.*}(.*)':", msg)
            groups = match.groups()
            fields.add(groups[0] if groups else msg)

        msgs = [_("{number}) {field} is invalid").format(number=i, field=f)
                for i, f in enumerate(fields, 1)]
        raise XmlValidationException('\n'.join(msgs))


class Signature(BaseTag):
    NAMESPACE = 'http://www.w3.org/2000/09/xmldsig#'

    def setup(self, inf):
        self.inf = inf
        c14n = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        ns = '{%s}' % self.NAMESPACE

        # Create SignedInfo tag.
        siginfo = etree.SubElement(self, ns + 'SignedInfo')
        etree.SubElement(siginfo, ns + 'CanonicalizationMethod', Algorithm=c14n)
        etree.SubElement(siginfo, ns + 'SignatureMethod',
                         Algorithm=self.NAMESPACE + 'rsa-sha1')

        # Create Reference tag.
        ref = etree.SubElement(siginfo, ns + 'Reference', URI='#' + inf.get('Id'))

        # Create Transform tag.
        trans = etree.SubElement(ref, ns + 'Transforms')
        etree.SubElement(trans, ns + 'Transform',
                         Algorithm=self.NAMESPACE + 'enveloped-signature')
        etree.SubElement(trans, ns + 'Transform', Algorithm=c14n)
        etree.SubElement(ref, ns + 'DigestMethod', Algorithm=self.NAMESPACE + 'sha1')
        self.digest = etree.SubElement(ref, ns + 'DigestValue')

        # Create SignatureValue tag.
        self.signature = etree.SubElement(self, ns + 'SignatureValue')

        # Create X509Data tag.
        keyinfo = etree.SubElement(self, ns + 'KeyInfo')
        x509 = etree.SubElement(keyinfo, ns + 'X509Data')
        self.cert = etree.SubElement(x509, ns + 'X509Certificate')
        return self

    def update(self, digest, signature, cert):
        self.digest.text = digest
        self.signature.text = signature
        self.cert.text = cert


class XmlSecSigner(object):

    def _create_tmp_cert(self, cert, password):
        with open(cert) as f:
            cert_file = f.read()

        # Reads the file in pkcs12 format how binary.
        pkcs12 = crypto.load_pkcs12(cert_file, password)
        cert = pkcs12.get_certificate()
        key = pkcs12.get_privatekey()
        p12 = crypto.PKCS12()
        p12.set_privatekey(key)
        p12.set_certificate(cert)

        with tempfile.NamedTemporaryFile(delete=False) as tmp_cert:
            tmp_cert.write(p12.export())

        return tmp_cert.name

    def get_signature(self, xml, cert, password_callback, certificate_callback):
        tmp_cert_path = self._create_tmp_cert(cert, str(password_callback()))
        # Tag to be signed.
        tag = xml[0].tag
        with tempfile.NamedTemporaryFile() as temp_xml:
            xml.export(temp_xml.name)
            cmd = ['xmlsec1', '--sign', '--pkcs12', tmp_cert_path, '--crypto',
                   'openssl', '--output', temp_xml.name, '--id-attr:Id', tag,
                   temp_xml.name]
            subprocess.call(cmd)
            signature = list(etree.parse(temp_xml.name).getroot())[-1]
        os.remove(tmp_cert_path)

        digest = signature.find('.//{*}DigestValue').text
        value = signature.find('.//{*}SignatureValue').text
        cert = signature.find('.//{*}X509Certificate').text
        return digest, value, cert


class CryptographySigner(object):

    def _get_key_cert(self, cert, password):
        with open(cert, 'rb') as f:
            pkcs12 = crypto.load_pkcs12(f.read(), str(password))

        private_key = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                             pkcs12.get_privatekey())
        key = load_pem_private_key(private_key, password=None, backend=default_backend())

        cert = crypto.dump_certificate(crypto.FILETYPE_PEM, pkcs12.get_certificate())
        cert = b'\n'.join(cert.split(b'\n')[1:-2])

        return key, cert

    def get_signature(self, xml, cert, password_callback, certificate_callback):
        assert has_cryptography
        key, cert = self._get_key_cert(cert, password_callback())

        # Digest
        digest = get_digest(xml[0])

        # Signature
        signed_info = copy.deepcopy(xml[-1][0])
        signed_info.find('.//{*}DigestValue').text = digest
        signer = key.signer(padding=PKCS1v15(), algorithm=SHA1())
        signer.update(get_c14n(signed_info))
        signature = base64.b64encode(signer.finalize())

        # Keep signature value compatible with xmlsec signer for testing purposes.
        signature = format_base64(signature)

        return digest, signature, cert.decode()


class PyKCS11Signer(object):

    def __init__(self):
        self._cert_label = None
        self._cert = None
        self._slot = None
        self._label = None

    def get_signature(self, xml, cert, password_callback, certificate_callback):
        _pkcs11 = PyKCS11.PyKCS11Lib()
        _pkcs11.load(cert)

        if self._slot is None:
            self._slot = _pkcs11.getSlotList()[0]
        if self._label is None:
            info = _pkcs11.getTokenInfo(self._slot)
            self._label = info.label.strip()

        session = _pkcs11.openSession(
            self._slot, PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION)

        retry = False
        for i in range(3):
            password = password_callback(self._label, retry=retry)
            try:
                session.login(str(password))
            except PyKCS11.PyKCS11Error:
                retry = True
            else:
                break
        else:
            # TODO: Abort the operation
            session.closeSession()
            raise Exception("Incorrect password")

        # find private key and compute signature
        priv_keys = session.findObjects(
            [(PyKCS11.CKA_CLASS, PyKCS11.CKO_PRIVATE_KEY),
             (PyKCS11.CKA_KEY_TYPE, PyKCS11.CKK_RSA)])

        priv_keys_dict = {}
        for priv_key in priv_keys:
            key_id, key_lbl = session.getAttributeValue(
                priv_key, [PyKCS11.CKA_ID, PyKCS11.CKA_LABEL])
            # Get the label the same way as NSS does
            priv_keys_dict['%s:%s' % (self._label, key_lbl)] = (key_id, priv_key)

        key_lbl = certificate_callback(list(priv_keys_dict.keys()))
        key_id, priv_key = priv_keys_dict[key_lbl]

        # Cert
        if self._cert is None or self._cert_label != key_lbl:
            x509_key = session.findObjects(
                [(PyKCS11.CKA_CLASS, PyKCS11.CKO_CERTIFICATE),
                 (PyKCS11.CKA_CERTIFICATE_TYPE, PyKCS11.CKC_X_509),
                 (PyKCS11.CKA_ID, key_id)])[0]
            self._cert = base64.b64encode(
                bytearray(session.getAttributeValue(x509_key, [PyKCS11.CKA_VALUE])[0]))

        self._cert_label = key_lbl

        # Digest
        digest = get_digest(xml[0])

        # Signature
        signed_info = copy.deepcopy(xml[-1][0])
        signed_info.find('.//{*}DigestValue').text = digest
        to_sign = get_c14n(signed_info)

        signature = session.sign(priv_key, to_sign,
                                 PyKCS11.Mechanism(PyKCS11.CKM_SHA1_RSA_PKCS, None))
        signature = base64.b64encode(bytearray(signature))

        # Logout and close the session. Can't leave it open or else
        # we would cause problems when usig NssSession again
        session.logout()
        session.closeSession()

        # Some certificates don't play well with nss if they are not properly unloaded.
        # PyKCS11 only unloads the library if it gets deleted, so that why we are
        # forcing it here. Unfortunately, this adds around 10 seconds per emission
        # process.
        del _pkcs11

        return digest, format_base64(signature), format_base64(self._cert)


_signers = {
    Certificate.TYPE_PKCS12: (CryptographySigner()
                              if has_cryptography else
                              XmlSecSigner()),
    Certificate.TYPE_PKCS11: PyKCS11Signer(),
}


def get_signer(cert_type):
    return _signers[cert_type]


def format_number(value, size=2):
    return str(value).rjust(size, '0')


def format_value(value, precision=2):
    _format = Decimal('10e-%d' % precision)
    return value.quantize(_format)


def format_datetime(date):
    return date.replace(tzinfo=tzlocal(), microsecond=0).isoformat()


def get_c14n(node):
    payload = etree.tostring(node, method="c14n", exclusive=False,
                             with_comments=False,
                             inclusive_ns_prefixes=None)
    return payload.replace(b' xmlns=""', b'')


def get_digest(node):
    sha1 = hashlib.sha1()
    sha1.update(get_c14n(node))
    return base64.b64encode(sha1.digest()).decode()


def format_base64(string):
    if isinstance(string, bytes):
        string = string.decode()
    return '\n'.join(string[i:i + 64] for i in range(0, len(string), 64))
