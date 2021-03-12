.. _networking-hc:

HyCon Serial (USB/RS-232) over TCP/IP
=====================================

On the machine where the HyCon board is attached to, run something like ``socat``
or for instance the ``tcp_serial_redirect.py`` which is shipped with ``PySerial``
and can be obtained from
https://raw.githubusercontent.com/pyserial/pyserial/master/examples/tcp_serial_redirect.py

Other Unix binaries which can be used are for instance ``socat``
https://bloggerbust.ca/post/let-socket-cat-be-thy-glue-over-serial/
or ``netcat``.

Next, put a script like the following at that machine (now refered to as
the server):

::

    #!/bin/bash -x
    source ~/.bash_profile
    cd "$(dirname $0)"
    /usr/local/bin/python3 tcp_serial_redirect.py -P 12345 /dev/cu.usbserial-DN050L1O 115200

Then, from the client machine, run something like

::

    ssh -L 12345:localhost:12345 ac /path/to/the/ac-bridge/run-bridge.sh

Where ``run-bridge.sh`` contains that script above.
Now you can connect to TCP port ``12345`` at the client machine in order to speak directly
with the HyCon. This works remarkably well, also TCP buffering or network latency is not
a problem at all for me even with Bernds slow internet connection :-)


.. note::

  **Known bugs**: When quitting the ssh session, the bridge is sometimes not killed properly.
  In this case, log into the server and kill the script directly, for instance with
  the following command:
  
  ::
  
      ps aux | grep tcp_serial_redirect | awk '{print $2}' | xargs kill
