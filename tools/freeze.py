# Script to used to create a standalone distribution of Stoq
import sys

import bbfreeze.recipes
from bbfreeze import main

# Disable this quite useless recipe which
# contains a list of libraries not to include.
# We don't want to skip a few arbitrary libs when
# we already ship webkit and everything.
del bbfreeze.recipes.recipe_gtk_and_friends

# List the scripts that we need wrappers for
sys.argv = [sys.argv[0],
            'bin/stoq',
            'bin/stoq-daemon',
            'bin/stoqdbadmin']
main()
