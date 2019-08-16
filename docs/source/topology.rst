.. _topology:

Topology
========

When you create or open a project, you can modify the topology
with the command ``edit``.
An empty topology looks like that :

.. code-block:: ini

    [config]
    image_dir = images
    config_dir = configs

    [nodes]

    [switches]

    [bridges]

The content of each section is explained below.

Nodes
-----

In the section ``[nodes]``, you can add host/routeur in the topology.
At minimum, each node is identified by :

  1. a name
  2. a type
  3. a number of interface and for each interface,

These 3 informations are declared like that :

.. code-block:: ini

    [nodes]
    [[host_name]]
    type = host_type
    if_numbers = 1
    if0 = remote_peer

3 main types of node are available in pynetem :

  1. docker node
  2. qemu node
  3. junos node

Docker node
```````````
A docker node is a docker container launch by pynetem based on 3 images :
  - rca/host identified by the type *docker.host*,
    which emulates a terminal node
  - rca/frr identified by the type *docker.frr*, which eumlates router
    based on the software `FRR <https://frrouting.org/>`_
  - rca/quagga identified by the type *docker.quagga*, which emulates router
    based on the software `Quagga <https://www.quagga.net/>`_

When possible, this is the prefered way to emulate node/router.

Qemu node
```````````
A qemu node is a qemu instance launch by pynetem. To add a qemu node in
the topology, the *type* parameter has to respect this form:

  * ``qemu.<image_name>`` where *<image_name>" is a name of a qemu image
    available in the folder designated by the config argument *image_dir*

Moreover, qemu node requires more argument than docker one:

  * ``console`` (required): the port number used to access to this instance
    throught telnet. It must be unique
  * ``memory`` (optional): specify this parameter (as a number, the unit is M)
    if you want to override the default value of memory allocated
    for a qemu instance.

Example
"""""""
If you configure *image_dir* equal to ``/opt/pynetem`` and a qemu image
is located at ``/opt/pynetem/stretch.img``, then you can add a qemu node
in the topology with the following lines:

.. code-block:: ini

    [nodes]
    [[host1]]
    type = qemu.stretch
    console = 2001
    memory = 256
    if_numbers = 1
    if0 = remote_peer

Junos node
```````````
Junos node is a specific qemu node used to launch Juniper JunOS olive image.
To use it, you have to get a JunOS olive image located in the *image_dir*
folder and naming ``junos-<version>.img``. Then you can declare a JunOS if you
specify the type ``junos.<version>``. The other argument is identical to
a qemu node.

The main differnce between an qemu and junos node concern the way
the state of the node is saved/loaded. For a junos node, only the
juniper configuration is saved as plain text in the project archive
(instead of complete img of the disk, like other qemu nodes), thanks
to a tenel connection.


Connections
```````````
TBD


Switches
--------
TBD

Bridges
-------
TBD
