import errno
import os
import sys

os.environ['LANGUAGE'] = 'pt_BR.UTF-8'

logdir = os.path.join(os.environ['APPDATA'], "stoq", "logs")
if not os.path.exists(logdir):
    os.makedirs(logdir)
# http://www.py2exe.org/index.cgi/StderrLog
for name in ['stdout', 'stderr']:
    filename = os.path.join(logdir, name + ".log")
    try:
        fp = open(filename, "w")
    except IOError, e:
        if e.errno != errno.EACCES:
            raise
        fp = open(os.devnull, "w")
    setattr(sys, name, fp)

os.environ['PATH'] += os.pathsep + "bin"

from stoq.main import main
sys.exit(main(sys.argv))
