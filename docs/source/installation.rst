.. _installation:

Installation/Configuration
==========================

Requirements
------------
To run pynetem, you have to install the following programs/modules
 * python3 (version >= 3.5.0)
 * python3-configobj
 * python3-pyroute2
 * `Docker CE <https://docs.docker.com/install/>`_
 * openvswitch-switch
 * uml-utilities
 * qemu (optional)
 * vde2 (optional)

Installation
------------
You can install PyNetem with the following command:

.. code-block:: bash

    $ python3 setup.py install

Debian Package
--------------

A debian package can be built for pynetem, thanks to files included in the
debian folder. To build the package, you can use for example pbuilder/pdebuild
utilities (https://pbuilder.alioth.debian.org/)

Configuration
-------------

After the installation, the configuration of pynetem is done with the file
``/etc/pynetem.conf``. Below, you will find the configuration by default :

.. code-block:: ini

    [general]
    daemon_socket = /tmp/pynetem-socket.ctl
    # the path where all qemu/junos images are stored
    image_dir = /home/pynetem
    # the command used to launch a console to access to host/router
    terminal = xterm -xrm 'XTerm.vt100.allowTitleOps: false' -title %(title)s -e %(cmd)s
    # the editor used to update the topology file
    editor = vim

    [qemu]
    # the memory by default for a qemu instance
    # it can be override in the topology file
    memory = 256
    # set to false to disable kvm when a qemu instance is launch
    enable_kvm = yes
