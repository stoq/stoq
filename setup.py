#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install_data import install_data
import glob

from kiwi.dist import (TemplateInstallLib, compile_po_files, listfiles,
     listpackages)

PACKAGE = 'stoq'
VERSION = '0.2.0'
 
class StoqInstallData(install_data):
    def run(self):
        self.data_files.extend(compile_po_files(PACKAGE))
        install_data.run(self)

class StoqInstallLib(TemplateInstallLib):
    name = PACKAGE
    resources = dict(locale='$prefix/share/locale',
                     docs='$prefix/share/doc/stoq',
                     basedir='$prefix')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            glade='$datadir/glade')

data_files = [
    ('share/stoq/pixmaps',
     listfiles('pixmaps', '*.xpm') +
     listfiles('pixmaps', '*.jpg') +
     listfiles('pixmaps', '*.png')),
    ('share/stoq/sbin', ('sbin/init-database', 'sbin/update-database')),
    ('share/doc/stoq', listfiles('docs/domain', '*.txt') +
     ['docs/AUTHORS', 'docs/CONTRIBUTORS', 'docs/COPYING',
      'docs/README']),
    ('share/stoq/glade',
     glob.glob('stoq/gui/*/glade/*.glade')),
    ]

setup(name=PACKAGE,
      version=VERSION,
      author='Async Open Source',
      author_email='evandro@async.com.br',
      url='http://www.async.com.br/projects/stoq/wiki',
      license='GPL',
      packages=listpackages('stoq'),
      scripts=['bin/stoq'],
      data_files=data_files,
      cmdclass=dict(install_lib=StoqInstallLib,
                    install_data=StoqInstallData))

