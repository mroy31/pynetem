PyNetem
=======

Description
-----------
PyNetem is a network emulator written in python based on
 * Qemu for emulate nodes (host or router)
 * Vde or OpenvSwitch for emulate hub/switch

Requirements
------------
 * Python >= 3.4
 * python3-configobj
 * qemu
 * vde2
 * openvswitch-switch

Installation
------------
You can install PyNetem with the following command:

    $python3 setup.py install

You can also build a debian package with pdebbuild if you prefer.

Usage
-----
To use PyNetmem, firstly you have lo launch pynetmem-daemon with the root
right. You can use the following command for example:

    $sudo pynetmem-daemon -n

Then you can use pynetem-emulator to create/launch project. For example:

    $pynetmem-emulator ./myproject.pnet
    $[net-emulator] edit # if you want to edit the topology
    $[net-emulator] reload # to reload the new topology
    $[net-emulator] console all # to open all consoles
    $[net-emulator] quit

Topology
--------
An example of topology is available in the file doc/example.net
