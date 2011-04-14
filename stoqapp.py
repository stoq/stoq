import sys
import os

os.environ['LANGUAGE'] = 'pt_BR.UTF-8'

from stoq.main import main
sys.exit(main(sys.argv))
