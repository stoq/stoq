# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
"""Utils for working with pickle"""

import errno
import cPickle
import glob
import hashlib
import os
import shutil
import sys
import tempfile

import giscanner

_CACHE_VERSION_FILENAME = '.cache-version'

def _get_versionhash():
    toplevel = os.path.dirname(giscanner.__file__)
    # Use pyc instead of py to avoid extra IO
    sources = glob.glob(os.path.join(toplevel, '*.pyc'))
    sources.append(sys.argv[0])
    # Using mtimes is a bit (5x) faster than hashing the file contents
    mtimes = (str(os.stat(source).st_mtime) for source in sources)
    return hashlib.sha1(''.join(mtimes)).hexdigest()

def _get_cachedir():
    homedir = os.environ.get('HOME')
    if homedir is None:
        return None
    if not os.path.exists(homedir):
        return None

    cachedir = os.path.join(homedir, '.cache')
    if not os.path.exists(cachedir):
        try:
            os.mkdir(cachedir, 0755)
        except OSError:
            return None

    scannerdir = os.path.join(cachedir, 'g-ir-scanner')
    if not os.path.exists(scannerdir):
        try:
            os.mkdir(scannerdir, 0755)
        except OSError:
            return None
    # If it exists and is a file, don't cache at all
    elif not os.path.isdir(scannerdir):
        return None
    return scannerdir


class CacheStore(object):

    def __init__(self):
        try:
            self._directory = _get_cachedir()
        except OSError, e:
            if e.errno != errno.EPERM:
                raise
            self._directory = None

        self._check_cache_version()

    def _check_cache_version(self):
        if self._directory is None:
            return

        current_hash = _get_versionhash()
        version = os.path.join(self._directory, _CACHE_VERSION_FILENAME)
        try:
            cache_hash = open(version).read()
        except IOError, e:
            # File does not exist
            if e.errno == errno.ENOENT:
                cache_hash = 0
            else:
                raise

        if current_hash == cache_hash:
            return

        self._clean()
        try:
            fp = open(version, 'w')
        except IOError, e:
            # Permission denied
            if e.errno == errno.EACCES:
                return
            else:
                raise

        fp.write(current_hash)

    def _get_filename(self, filename):
        # If we couldn't create the directory we're probably
        # on a read only home directory where we just disable
        # the cache all together.
        if self._directory is None:
            return
        hexdigest = hashlib.sha1(filename).hexdigest()
        return os.path.join(self._directory, hexdigest)

    def _cache_is_valid(self, store_filename, filename):
        return (os.stat(store_filename).st_mtime >=
                os.stat(filename).st_mtime)

    def _remove_filename(self, filename):
        try:
            os.unlink(filename)
        except IOError, e:
            # Permission denied
            if e.errno == errno.EACCES:
                return
            else:
                raise
        except OSError, e:
            # File does not exist
            if e.errno == errno.ENOENT:
                return
            else:
                raise

    def _clean(self):
        for filename in os.listdir(self._directory):
            if filename == _CACHE_VERSION_FILENAME:
                continue
            self._remove_filename(os.path.join(self._directory, filename))

    def store(self, filename, data):
        store_filename = self._get_filename(filename)
        if store_filename is None:
            return

        if (os.path.exists(store_filename) and
            self._cache_is_valid(store_filename, filename)):
            return None

        tmp_fd, tmp_filename = tempfile.mkstemp(prefix='g-ir-scanner-cache-')
        try:
            cPickle.dump(data, os.fdopen(tmp_fd, 'w'))
        except IOError, e:
            # No space left on device
            if e.errno == errno.ENOSPC:
                self._remove_filename(tmp_filename)
                return
            else:
                raise

        try:
            shutil.move(tmp_filename, store_filename)
        except IOError, e:
            # Permission denied
            if e.errno == errno.EACCES:
                self._remove_filename(tmp_filename)
            else:
                raise

    def load(self, filename):
        store_filename = self._get_filename(filename)
        if store_filename is None:
            return
        try:
            fd = open(store_filename)
        except IOError, e:
            if e.errno == errno.ENOENT:
                return None
            else:
                raise
        if not self._cache_is_valid(store_filename, filename):
            return None
        try:
            data = cPickle.load(fd)
        except (AttributeError, EOFError, ValueError, cPickle.BadPickleGet):
            # Broken cache entry, remove it
            self._remove_filename(store_filename)
            data = None
        return data

