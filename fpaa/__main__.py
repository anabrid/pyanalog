# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the FPAA module of the PyAnalog toolkit.
#
# ANABRID_BEGIN_LICENSE:GPL
# ANABRID_END_LICENSE
#

"""
A Command Line Interface (CLI) for PyFPAA.
"""

from .fpaa import cli

if __name__ == "__main__":
    # should run some "Deprecated" notice because this is supposed to be run
    # with python -m dda
    pass
 
cli()
