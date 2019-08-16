PyNetem
=======

Description
-----------
PyNetem is a network emulator written in python based on
 * Qemu or docker for emulate nodes (host or router)
 * Vde or OpenvSwitch for emulate hub/switch

Requirements
------------
 * Python >= 3.5
 * python3-configobj
 * python3-pyroute2
 * docker-ce
 * openvswitch-switch
 * uml-utilities
 * qemu (optional)
 * vde2 (optional)

Installation
------------
You can install PyNetem with the following command:

    $python3 setup.py install

You can also build a debian package with pdebbuild if you prefer.

Configuration
-------------

After the installation, the configuration of pynetem is done with the file
/etc/pynetem.conf.

Usage
-----
To use PyNetmem, firstly you have lo launch pynetmem-daemon with the root
right. You can use the following command for example:

    $sudo pynetmem-daemon -n

Then you can use pynetem-emulator to create/launch project. For example to create a project:

    $pynetmem-emulator --new ./myproject.pnet
    $[net-emulator] edit # if you want to edit the topology
    $[net-emulator] reload # to reload the new topology
    $[net-emulator] console all # to open all consoles
    $[net-emulator] quit

Topology
--------
An example of topology is available in the file example/topology.net

Docker Node
-----------
To use docker, you need to build expected images.
 * rca/quagga
 * rca/frr
 * rca/host

To do that, you need to use the command docker build, for example

    $ cd docker/host
    $ docker build -t rca/host .

Or, if you want to build all the docker image, you can use the script
build.sh available in the docker directory.

Junos Router
------------
PyNetem has a special mode to emulate junos router. In the topology file, you
need to use junos.<version> as node type. In this case, the configuration is
saved as plain text (instead of complete img of the disk), thanks to a
telnet connection.

Documentation
-------------
For more details about pynetem, see the documentation available here :
https://pynetem.readthedocs.io/en/latest/
