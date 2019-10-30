.. _commands:

Commands
========

This page do the list of all commands available in the pynetem console.

quit
----
Quit the pynetem console.

run
----
If the project has not been launch during pynetem starting, run this command to
load the topology and start all the nodes.


save
----
Save the project. This command does two things:
  - save the current topology
  - for each running node, save the current of the node

config
------
Save all the node config files in a specific folder.

Usage:

.. code-block:: bash

  config <dest_path>

check
-----
Check that the topology file is correct. If not, return found errors

capture
-------
Capture trafic on the given node interface with
`Wireshark <https://www.wireshark.org/>` (must be installed first)

Usage:

.. code-block:: bash

  capture <node_name>.<if_number>
  # example
  capture R1.0

reload
------
Reload the project. You have to run this command after modifing the
topology. It does the following actions:

  - Stop all running swithes/nodes/bridges
  - Load the new topology
  - Start all switches/nodes/bridges

edit
----
Edit the topology. The editor used to open the topology file is configured
by the parameter ``editor`` in the configuration file (by default,
it is vim).

view
----
View the content of the topology file.

status
------
Display the status of the project/topology

start
-----
Start a node or all the nodes

Usage:

.. code-block:: bash

  # start one node
  start <node_name>
  # start all the nodes
  start all

stop
----
Stop a node or all the nodes. Same principle than *start* command.

restart
-------
Restart a node or all the nodes. Same principle than *start* command.

console
-------
Open a console for a node (specifing by the *node's name*) or all the nodes
(specifing by *all*). The terminal command used to open the console
can be modified with the config parameter ``terminal``. By default,
the command used is:

.. code-block:: bash

  xterm -xrm 'XTerm.vt100.allowTitleOps: false' -title %(title)s -e %(cmd)s

The kind of console opened by this command depends on the type of node:

  * For qemu node and docker host node: ``bash``
  * For docker.frr and docker.quagga, run directly ``vtysh``

debug
-----
Same as *console* command, except run ``bash`` command whatever the node.

ifstate
-------
Enable/disable a node interface.

Usage:

.. code-block:: bash

  ifstate <node_name>/<if_number> up|down
  # example
  ifstate R1.0 down
