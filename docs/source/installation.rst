.. _installation:

Installation
============

Requirements
------------
To run pynetem, you have to install the following programs/modules
 * python >= 3.5
 * python3-cmd2 >= 0.7.0
 * python3-configobj
 * python3-pyroute2
 * python3-docker
 * docker-ce
 * openvswitch-switch
 * uml-utilities
 * wireshark
 * xterm
 * bridge-utils
 * qemu (optional)
 * telnet (optional)
 * vde2 (optional)

Manual Installation
-------------------
You can install PyNetem with the following command (with superuser privileges):

.. code-block:: bash

    $ python3 setup.py install

Debian Package
--------------

Debian packages are available on `github <https://github.com/mroy31/pynetem/releases>`_
for the following distribution :
  * Debian buster
  * Debian stretch
  * Ubuntu LTS focal
  * Ubuntu LTS bionic

If your distribution is not in the list, you can build a package for pynetem,
thanks to files included in the debian folder.
To build the package, you can use for example pbuilder/pdebuild
utilities (https://pbuilder.alioth.debian.org/)

Once you have downloaded the correct package, you can install it
with the following commands :

.. code-block:: bash

    $ sudo apt install gdebi-core
    $ sudo gdebi pynetem_<version>_all.deb

Then you need enable and start the daemon with the following commands

.. code-block:: bash

    $ sudo systemctl enable pynetem.service
    $ sudo systemctl start pynetem.service
