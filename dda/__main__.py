"""
A Command Line Interface (CLI) for PyDDA.
"""

from .dsl import cli_exporter

if __name__ == "__main__":
    # should run some "Deprecated" notice because this is supposed to be run
    # with python -m dda
    pass
 
cli_exporter()
