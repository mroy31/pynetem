.. _installation:

Installation
============

Requirements
------------
To run pynetem, you have to install the following programs/modules
 * python3 (version >= 3.5.0)
 * python3-configobj
 * python3-pyroute2
 * DockerCE_
 * openvswitch-switch
 * uml-utilities
 * qemu (optional)
 * vde2 (optional)

.. _DockerCE: https://docs.docker.com/install/

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
