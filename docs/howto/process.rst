Stoq development process
========================

Git
---

Git is a versioning control system that we use for Stoq.
It has been well documented in other places and we will explain the very
basics in this tutorial.

The commands you need to use on a daily basis are::

  git add
  git commit
  git diff
  git review
  git rebase
  git show

XXX: links to books.

Gerrit
------

Gerrit is a review tool that is used by Stoq. It can be found at:

  * `http://gerrit.async.com.br/ <http://gerrit.async.com.br/>`_

Creating an account
+++++++++++++++++++

To be able to submit and review patches you need to create an account on
the Stoq gerrit instance.

Login to `http://gerrit.async.com.br/ <http://gerrit.async.com.br/>`_ and click
on the **Register** link in the top right corner.

It will ask you for an OpenID account such as Google. Select your provider,
and make sure you allow gerrit.stoq.com.br to access your profile.

Choosing a username
+++++++++++++++++++

To be able to use gerrit via the git command line tools you need to configure
a username. If you didn't do that in the previous section, go to:

**Gerrit** -> **Settings** -> **Profile** and write something in the username field.

Note: This should be the same as the username on your computer, so that git and
git-review can pick it up when connecting to gerrit.

Attaching an SSH key
++++++++++++++++++++

After registering you need to attach an SSH key.
This is used to verify access via the command line tools, to identify yourself.

To generate a new SSH key, enter the code below. We want the default settings so when asked to enter a file in which to save the key, just press enter.::

  ssh-keygen -t rsa -C "your_email@youremail.com"

Assign the pass phrase (press [enter] key twice if you don't want a passphrase).

It will create 2 files in ~/.ssh directory as follows::

  ~/.ssh/id_rsa : identification (private) key
  ~/.ssh/id_rsa.pub : public key

This is your public SSH key. You may need to turn on “view hidden files” to find it because the .ssh directory is hidden. It’s important you copy your SSH key exactly as it is written without adding any newlines or whitespace. Now paste it into the “Key” field.

Add your SSH key::

  cat /home/preilly/.ssh/id_rsa.pub

Copy the contents and go to **Gerrit** -> **Settings** -> **SSH Public Keys** and add it.

Git-review
----------

XXX

Modifying the source code
-------------------------

Showing your changes
--------------------

Committing your changes
-----------------------

Submitting a patch
------------------

XXX

Updating a reviewed patch
-------------------------

XXX

Listing your patches
--------------------

XXX

Jenkins CI
----------

XXX

Examining the output
++++++++++++++++++++

XXX

Retriggering a change
+++++++++++++++++++++

XXX

