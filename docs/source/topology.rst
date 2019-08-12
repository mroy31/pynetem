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

In the section ``[nodes]``, you can host/routeur. At minimum, each node is
identified by :

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

