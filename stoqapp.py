import errno
import os
import sys

os.environ['LANGUAGE'] = 'pt_BR.UTF-8'

from stoqlib.lib.osutils import get_application_dir
stoqdir = get_application_dir()

# http://www.py2exe.org/index.cgi/StderrLog
for name in ['stdout', 'stderr']:
    filename = os.path.join(stoqdir, "logs", name + ".log")
    try:
        fp = open(filename, "w")
    except IOError, e:
        if e.errno != errno.EACCES:
            raise
        fp = open(os.devnull, "w")
    setattr(sys, name, fp)

from stoq.main import main
sys.exit(main(sys.argv))
