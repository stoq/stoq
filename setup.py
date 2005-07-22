#!/usr/bin/env python
from fnmatch import fnmatch
import os
from distutils.core import setup

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

setup(name="stoqlib",
      version="0.1.0",
      author="Async Open Source",
      author_email="evandro@async.com.br",
      url="http://www.async.com.br/projects/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[
        ('share/stoqlib/pixmaps',
         listfiles('stoqlib', 'gui', 'pixmaps', '*.xpm')),
        ('share/stoqlib/pixmaps',
         listfiles('stoqlib', 'gui', 'pixmaps', '*.png')),
        ('share/stoqlib/glade',
         listfiles('stoqlib', 'gui', 'glade', '*.glade')),
        ],
    packages=['stoqlib',
              'stoqlib.gui',
              'stoqlib.reporting'],
    )
