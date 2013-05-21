Development setup
=================

FIXME: Write a small introduction git and git-review and how the interact with
gerrit.

Download git-stoq
-----------------

As the first pass, we need to download a script that checks out the stoq sources
from the main repository::

  mkdir ~/bin/
  wget https://raw.github.com/stoq/git-stoq/master/git-stoq -O ~/bin/git-stoq
  chmod +x ~/bin/git-stoq

Make sure you add ~/bin/ to the PATH inside your .bashrc, then you can type just::

  git stoq

In the future when you want to invoke git-stoq.

Checking out the sources
------------------------

If you've installed git-stoq properly, you can just type::

  git stoq --setup

Which will ask you where to save the developer repositories, just press Enter.

Then you need to create the initial branch::

  git-stoq --init master

Configure GIT
-------------

Git tracks who makes each commit by checking the user’s name and email. In addition, we use this info to associate your commits with your gerrit account. To set these, enter the code below, replacing the name and email with your own.::

  git config --global user.email "XXX@example.com"
  git config --global user.name "Marcelo Fulano"

