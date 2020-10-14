Stoq
====

Stoq's homepage is located at:

  https://www.stoq.com.br/

You can fetch the latest source code from github:

  $ git clone https://github.com/stoq/stoq.git


Installation for development
============================

To install stoq you have to install Poetry_ and run::

    $ poetry install


Then check everything has been installed correctly run the tests::

    $ make test


And see if stoqdbadmin has been provided::

    $ stoqdbadmin help


Mailing list
============

There is two mailing lists for Stoq. You can subscribe to them through the web
interface at:

http://www.async.com.br/mailman/listinfo/stoq-users
http://www.async.com.br/mailman/listinfo/stoq-devel


Copyright Information
=====================

Stoq itself is covered by the GNU General Public License
(version 2.0, or if you choose, a later version).  Basically just don't
say you wrote bits you didn't.

However, some parts of it are covered under different licesenses, see:

docs/copyright for more information


.. _Poetry: https://github.com/python-poetry/poetry/
