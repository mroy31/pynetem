.. _commands:

Commands
========

This page lists all commands available in the pynetem console.

capture
-------
Capture trafic on the given node interface with
`Wireshark <https://www.wireshark.org/>` (must be installed first)

Usage:

.. code-block:: bash

  capture <node_name>.<if_number>
  # example
  capture R1.0

**Warning:**

When you want to capture on an interface of qemu/junos node, the user
that launches pynetem-emulator must have the right to capture trafic
with wireshark (on debian like system, this user has to be a member
of *wireshark* group)

check
-----
Check that the topology file is correct. If not, return found errors

config
------
Save all the node config files in a specific folder.

Usage:

.. code-block:: bash

  config <dest_path>

copy
----
Copy files/folder between a docker node and the host fs or vice versa.

Usage:

.. code-block:: bash

  copy node:/mypath/myfile.txt /hostpath/

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
  * For docker frr node, run directly ``vtysh``

edit
----
Edit the topology. The editor used to open the topology file is configured
by the parameter ``editor`` in the configuration file (by default,
it is vim).

ifstate
-------
Enable/disable a node interface.

Usage:

.. code-block:: bash

  ifstate <node_name>/<if_number> up|down
  # example
  ifstate R1.0 down

quit
----
Quit the pynetem console.

reload
------
Reload the project. You have to run this command after modifing the
topology. It does the following actions:

  - Stop all running swithes/nodes/bridges
  - Load the new topology
  - Start all switches/nodes/bridges

restart
-------
Restart a node or all the nodes. Same principle than *start* command.

run
----
If the project has not been launch during pynetem starting, run this command to
load the topology and start all the nodes.


save
----
Save the project. This command does two things:
  - save the current topology
  - for each running node, save the current of the node

shell
-----
Same as *console* command, except run ``bash`` command whatever the node.

start
-----
Start a node or all the nodes

Usage:

.. code-block:: bash

  # start one node
  start <node_name>
  # start all the nodes
  start all

status
------
Display the status of the project/topology

stop
----
Stop a node or all the nodes. Same principle than *start* command.

Usage:

.. code-block:: bash

  # stop one node
  stop <node_name>
  # stop all the nodes
  stop all

view
----
View the content of the topology file.
