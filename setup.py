#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install_data import install_data

from kiwi.dist import (TemplateInstallLib, compile_po_files, listfiles,
     listpackages)

from stoq import __version__

PACKAGE = 'stoq'

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
                            glade='$datadir/glade',
                            config='$sysconfdir/stoq')

data_files = [
    ('share/stoq/pixmaps',
     listfiles('data/pixmaps', '*.png')),
    ('share/stoq/bin',  ['bin/init-database']),
    ('etc/stoq',  ''),
    ('share/doc/stoq',
     ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'README', 'NEWS']),
    ('share/stoq/glade',
     listfiles('data', '*.glade')),
    ]

setup(name=PACKAGE,
      version=__version__,
      author='Async Open Source',
      author_email='evandro@async.com.br',
      url='http://www.async.com.br/projects/stoq/wiki',
      license='GPL',
      packages=listpackages(PACKAGE),
      scripts=['bin/stoq'],
      data_files=data_files,
      cmdclass=dict(install_lib=StoqInstallLib,
                    install_data=StoqInstallData))

