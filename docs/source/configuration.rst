.. _configuration:

Configuration
=============

Configuration file
------------------
After the installation, the configuration of pynetem is done with the file
``/etc/pynetem.conf``. Below, you will find the configuration by default :

.. code-block:: ini

    [general]
    daemon_socket = /tmp/pynetem-socket.ctl
    # the path where all qemu/junos images are stored
    image_dir = /home/pynetem
    # the command used to launch a console to access to host/router
    terminal = xterm -xrm 'XTerm.vt100.allowTitleOps: false' -title %(title)s -e %(cmd)s
    # the editor used to update the topology file
    editor = vim

    [qemu]
    # the memory by default for a qemu instance
    # it can be override in the topology file
    memory = 256
    # set to false to disable kvm when a qemu instance is launch
    enable_kvm = yes

    [docker]
    # docker image names used by default for docker node
    # tag must be equal to pynetem version
    frr_img = mroy31/pynetem-frr
    host_img = mroy31/pynetem-host
    server_img = mroy31/pynetem-server

Daemon
------
If you install pynetem manually, you have lo launch pynetmem-daemon with the root
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

If you use debian package, pynetem-daemon is launch thanks to systemd.


Pull docker images
------------------

If you plan to use docker nodes, you need to pull images built for pynetem
and available on docker hub. For that, you can use the following command:

.. code-block:: bash

    $ sudo pynetmem-emulator --pull

You can verify the image installation with the following command:

.. code-block:: bash

    $ sudo docker image ls
    REPOSITORY                TAG       IMAGE ID       CREATED             SIZE
    ...
    mroy31/pynetem-frr-enac   0.14.2    351a48e37994   About an hour ago   127MB
    mroy31/pynetem-server     0.14.2    e58af79d5ad9   3 hours ago         179MB
    mroy31/pynetem-host       0.14.2    01f7a34d4cf3   13 hours ago        284MB
