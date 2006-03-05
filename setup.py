#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install_data import install_data

from kiwi.dist import (KiwiInstallData, KiwiInstallLib, compile_po_files, 
     listfiles, listpackages)

from stoq import __version__

PACKAGE = 'stoq'

class StoqInstallData(KiwiInstallData):
    def run(self):
        self.data_files.extend(compile_po_files(PACKAGE))
        install_data.run(self)

class StoqInstallLib(KiwiInstallLib):
    resources = dict(locale='$prefix/share/locale',
                     docs='$prefix/share/doc/stoq',
                     basedir='$prefix')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            glade='$datadir/glade',
                            config='$sysconfdir/stoq')

data_files = [
    ('$datadir/pixmaps',
     listfiles('data/pixmaps', '*.png')),
    ('$datadir/bin',  ['bin/init-database']),
    ('$datadir/glade',
     listfiles('data', '*.glade')),
    ('$sysconfdir',  ''),
    ('share/doc/stoq',
     ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'README', 'NEWS']),
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

