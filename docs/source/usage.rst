.. _usage:

Usage
=====

Console
-------

Then you can use pynetem-emulator to create/launch project or to connect to
an existing running project (see client mode below).
For example to create a project:

.. code-block:: bash

    $ pynetmem-emulator --new ./myproject.pnet
    [net-emulator] edit # if you want to edit the topology
    [net-emulator] reload # to reload the new topology
    [net-emulator] console all # to open all consoles
    [net-emulator] quit # to quit pynetem

For more details, See
  * :ref:`topology` for more detail to build a network
  * :ref:`commands` for the list of available commands

Below, you will find available arguments to launch pynetem-emulator

.. code-block:: bash

    usage: pynetem-emulator [-h] [-c FILE] [-v] [-d] [--new] [--no-start]
                            [--clean]
                            [PRJ]

    positional arguments:
    PRJ                   Path for the pnet project

    optional arguments:
    -h, --help            show this help message and exit
    -c FILE, --conf-file FILE
                            Specify a custom conf file
    -v, --version         Display pynetem version and exit
    -d, --debug           Log more debug information
    --new                 Set to create a new project
    --no-start            Do not start the project at launch
    --clean               Clean the netem env
    --pull                Pull docker images
    --client-only         Connect to an launched pynetem-server
    -p P_NUMBER, --port P_NUMBER
                        Port number

Client mode
-----------

Since version 0.11, the core of pynetem has been splitted from the console.
Exactly, when you launch a project with pynetem, a TCP server has been launch
in background (on port 10100 by default, this value can be changed with
the -p parameter). Then each command enter in the console has been sent to the
server using a TCP connection.
Like that, if you accidentally close the terminal with your console, you can
reconnect to the opening server with the following command:

.. code-block:: bash

    $ pynetem-emulator --client-only

MPLS support
------------

Since version 0.14, pynetem supports MPLS with FRR docker image.
To work, you must enable MPLS features in linux kernel by loading
the following modules :

- mpls_iptunnel
- mpls_router
