#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the FPAA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# Commercial License Usage
# Licensees holding valid commercial anabrid licenses may use this file in
# accordance with the commercial license agreement provided with the
# Software or, alternatively, in accordance with the terms contained in
# a written agreement between you and Anabrid GmbH. For licensing terms
# and conditions see https://www.anabrid.com/licensing. For further
# information use the contact form at https://www.anabrid.com/contact.
# 
# GNU General Public License Usage
# Alternatively, this file may be used under the terms of the GNU 
# General Public License version 3 as published by the Free Software
# Foundation and appearing in the file LICENSE.GPL3 included in the
# packaging of this file. Please review the following information to
# ensure the GNU General Public License version 3 requirements
# will be met: https://www.gnu.org/licenses/gpl-3.0.html.
# ANABRID_END_LICENSE
#

"""
PyFPAA is a compiler for programmable analog computers (FPAAs). It was written by SvenK in Dec 2019
for quickly approaching a testing infrastructure for the XBAR module for the *Analog Paradigm M-1*
analog computer.

The script requires a (lengthy) machine description, which encodes the computational parts
available and is quite similar to a machine library in VHDL. That file encodes especially the
hard-wired vs. configurable parts of the machine.
The actual program is then rather short and describes how the configurable computational parts
are connected with each other. It also specifies constant coefficients which are set with
digital potentiometers or other digital steering parameters.

The output of the code is the analog computer configuration, as required by :mod:`hycon`. This can
be either

* a single line of text, which are mostly hexadecimal encoded
  instructions together with command characters, all following the serial console protocol which
  the HybridController of the machine expects (http://analogparadigm.com/downloads/hc_handbook.pdf).
* configuration tuples for :mod:`hycon`
* or a direct API to :mod:`hycon`

In order to run this program, all you need is ``PyYAML`` to read the YAML files. If you want
to draw circuit plots, you need ``matplotlib``.

Command line interface
----------------------

::

    % python -m fpaa --help
    usage: fpaa.py [-h] [-v] [-o OUTPUT.txt] [-p OUTPUT.pdf] (-A {XBAR-Only,AP-M1-Mini} | -a path/to/my/MACHINE.yml)
                CIRCUIT.yml

    A circuit synthesizer for the HyConAVR.

    positional arguments:
    CIRCUIT.yml           The YAML file holding the circuit description

    optional arguments:
    -h, --help            show this help message and exit
    -v, --verbose         increases log verbosity for each occurence.
    -o OUTPUT.txt, --output OUTPUT.txt
                            Put output string into file (default is '-' and means stdout)
    -p OUTPUT.pdf, --plot OUTPUT.pdf
                            Plot crossbar switch
    -A {XBAR-Only,AP-M1-Mini}, --registered-arch {XBAR-Only,AP-M1-Mini}
                            Target machine architecture description: Any YAML file in directory
                            /home/sven/Analog/Forschungsauftrag/dda/fpaa is available as machine
    -a path/to/my/MACHINE.yml, --arch path/to/my/MACHINE.yml
                            Target machine architecture description (any valid filename)

See :meth:`fpaa.cli()` for further details.
"""

# Populate namespace

from .fpaa import load_from_yaml, synthesize, compile_instructions
