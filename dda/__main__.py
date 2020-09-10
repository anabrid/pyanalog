#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the DDA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# ANABRID_END_LICENSE
#

"""
A Command Line Interface (CLI) for PyDDA.
"""

from .dsl import cli_exporter

if __name__ == "__main__":
    # should run some "Deprecated" notice because this is supposed to be run
    # with python -m dda
    pass
 
cli_exporter()
