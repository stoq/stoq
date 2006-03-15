#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Download and install the major stoq dependencies"""

#
# Dependency checking
#

import sys, os
# Required version of Python
REQUIRED_VERSION = (2, 4)

version_string = sys.version.split(' ')[0]
majmin = tuple(map(int, version_string.split('.')))
if majmin < REQUIRED_VERSION:
    raise SystemExit("ERROR: Python %s or higher is required to run Stoq, "
                     "%s found. Please, visit http://www.python.org/ and "
                     "install a new version."
                     % ('.'.join(map(str, REQUIRED_VERSION)), version_string))

DEFAULT_STOQ_VERSION = '0.7.0'
DEFAULT_URL = ("http://www.async.com.br/projects/stoq/dist/%s" %
               DEFAULT_STOQ_VERSION)

stoq_required_packages = [('kiwi', '1.9.7'),
                          ('gazpacho', '0.6.5'),
                          ('stoqdrivers', '0.3'),
                          ('stoqlib', DEFAULT_STOQ_VERSION),
                          ('stoq', DEFAULT_STOQ_VERSION)]


#
# Downloading and installing packages
#


import urllib2
import commands
import optparse
import tempfile, shutil


def fetch_packages(tmpdir):
    delay = 0
    print ("""
---------------------------------------------------------------------------
Downloading required packages for stoq. You may need to enable firewall
access for this script first.

(Note: if this machine does not have network access, please obtain the
 tar.gz files in

%s

and place it in this directory before rerunning this script.)
---------------------------------------------------------------------------"""
            % DEFAULT_URL)

    downloaded_packages = []
    for package_name, version in stoq_required_packages:
        filename = '%s-%s.tar.gz' % (package_name, version)
        url = '%s/%s' % (DEFAULT_URL, filename)
        file_path = os.path.join(tmpdir, filename)

        src = dst = None
        if not os.path.exists(file_path):# Avoiding repeated downloads
            try:
                print " Downloading file %s ... " % filename,
                sys.stdout.flush()
                src = urllib2.urlopen(url)
                # Read/write all in one block, so we don't create a corrupt file
                # if the download is interrupted.
                data = src.read()
                dst = open(file_path,"wb")
                dst.write(data)
                print "ok"
            finally:
                if src:
                    src.close()
                if dst:
                    dst.close()
        else:
            print " Found file %s in the current directory" % filename
        downloaded_packages.append((package_name, filename))
    return downloaded_packages


def get_parser():
    parser = optparse.OptionParser()
    parser.add_option('-c', '--currdir',
                      action="store",
                      dest="currdir",
                      help='Use current dir to store downloaded files')
    parser.add_option('-v', '--verbose',
                      action="store_true",
                      dest="verbose",
                      help='List all the download in details')
    parser.add_option('-p', '--prefix',
                      action="store",
                      dest="prefix",
                      help='Installation prefix')
    return parser


def install_packages(options, tmpdir):
    packages = fetch_packages(tmpdir)
    os.chdir(tmpdir)
    if options.prefix:
        prefix = "--prefix=%s" % options.prefix
        run_command = ('python setup.py install %s --quiet'
                       % prefix)
    else:
        run_command = 'python setup.py install --quiet'
    for package_name, file_name in packages:
        print ("Uncompressing file %s ... "
               % file_name),
        sys.stdout.flush()
        ret = commands.getstatusoutput('tar xfz %s' % file_name)
        if ret[0] == 256:
            raise SystemExit("Could not unpack file %s. The error message "
                             "is %s" % (file_name, ret[1]))
        print "ok"

        dirname = '%s/%s' % (tmpdir, file_name.replace('.tar.gz', ''))
        os.chdir(dirname)

        print "Installing package %s... " % package_name,
        sys.stdout.flush()
        ret = commands.getstatusoutput(run_command)
        if ret[0] == 256:
            raise SystemExit("Could not install package %s. The error "
                             "message is %s" % (package_name, ret[1]))
        print "ok"
        os.chdir(tmpdir)


def main(args):
    """Install stoq packages"""

    parser = get_parser()
    options, args = parser.parse_args(args)
    if options.currdir:
        tmpdir = options.currdir
    else:
        tmpdir = tempfile.mkdtemp(prefix="stoq_install-")

    try:
        install_packages(options, tmpdir)
    finally:
        if not options.currdir:
            shutil.rmtree(tmpdir)

    print "Stoq %s has been sucessfully installed." % DEFAULT_STOQ_VERSION


if __name__=='__main__':
    sys.exit(main(sys.argv[:]))
