.. _usage:

Usage
=====

Daemon
------
To use PyNetmem, firstly you have lo launch pynetmem-daemon with the root
right. It is required to execute commands that require privileges. You can use
the following command for example:

.. code-block:: bash

    $ sudo pynetmem-daemon -n

Below, you will find available arguments to launch pynetem-daemon

.. code-block:: bash

    usage: pynetem-daemon [-h] [-c FILE] [-d] [-n] [-l LOGFILE]

    optional arguments:
    -h, --help            show this help message and exit
    -c FILE, --conf-file FILE
                            Specify a custom conf file
    -d, --debug           Log more debug informations
    -n, --nodaemon        No daemonize pynetem daemon
    -l LOGFILE, --log-file LOGFILE

Client
------

Then you can use pynetem-emulator to create/launch project.
For example to create a project:

.. code-block:: bash

    $ pynetmem-emulator --new ./myproject.pnet
    [net-emulator] edit # if you want to edit the topology
    [net-emulator] reload # to reload the new topology
    [net-emulator] console all # to open all consoles
    [net-emulator] quit

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
    -d, --debug           Log more debug informations
    --new                 Set to create a new project
    --no-start            Do not start the project at launch
    --clean               Clean the netem env
