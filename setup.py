#!/usr/bin/env python
from distutils.command.install_data import install_data
from distutils.core import setup
from distutils.dep_util import newer
from distutils.log import info
from fnmatch import fnmatch
import os

class InstallData(install_data):
    def run(self):
        self.data_files.extend(self._compile_po_files())
        
        install_data.run(self)

    def _compile_po_files(self):
        data_files = []
        for po in listfiles('po', '*.po'):
            lang = os.path.basename(po[:-3])
            mo = os.path.join('locale', lang,
                              'LC_MESSAGES', 'stoqlib.mo')

            if not os.path.exists(mo) or newer(po, mo):
                directory = os.path.dirname(mo)
                if not os.path.exists(directory):
                    info("creating %s" % directory)
                    os.makedirs(directory)
                cmd = 'msgfmt -o %s %s' % (mo, po)
                info('compiling %s -> %s' % (po, mo))
                if os.system(cmd) != 0:
                    raise SystemExit("Error while running msgfmt")
            dest = os.path.dirname(os.path.join('share', mo))
            data_files.append((dest, [mo]))
            
        return data_files

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
         listfiles('stoqlib/gui/pixmaps', '*.xpm') +
         listfiles('stoqlib/gui/pixmaps', '*.png')),
        ('share/stoqlib/glade',
         listfiles('stoqlib/gui/glade', '*.glade')),
        ],
    packages=['stoqlib',
              'stoqlib.gui',
              'stoqlib.reporting'],
    cmdclass={'install_data': InstallData },
    )

