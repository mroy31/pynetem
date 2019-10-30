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
 * python3-cmd2 >= 0.7.0
 * python3-configobj
 * python3-pyroute2
 * docker-ce
 * openvswitch-switch
 * uml-utilities
 * wireshark
 * xterm
 * bridge-utils
 * qemu (optional)
 * telnet (optional)
 * vde2 (optional)

Installation
------------
You can install PyNetem with the following command (with superuser privileges):

    $python3 setup.py install

You can also build a debian package with pbuilder/sbuild if you prefer.

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
To use docker node, you need to build the images used by pynetem.
 * rca/quagga -> for emulate router based on quagga software
 * rca/frr -> for emulate router based on frr software
 * rca/host -> for emulate host

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
However, to use this kind of node, you need to put in the folder defined by 
the config parameter *image_dir*, a junos image working with qemu with 
a specific configuration: 
  * A super user named *juniper* with the password *Juniper*

Documentation
-------------
For more details about pynetem, see the documentation available here :
https://pynetem.readthedocs.io/en/latest/
