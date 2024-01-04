# PyAnalog: A Pythonic Analog Computer Demonstrator Interface

Welcome to PyAnalog, a *research code* written and maintained by 
[Anabrid GmbH](https://anabrid.com/) and released as Open Source
(see below for license).

This repository holds a Python package called `pyanalog`.
It consists of three modules/libraries which allow to interface
analog computers on a software developer/mathematican level:

* `PyDDA` is a tool for simple algebraic transformations of equations
  and circuits as well as their numerical simulation.
* `PyFPAA` is a tool for compiling an electrical circuit into a machine
  architecture. This especially sets digital potentiometers and
  cross bar switches and relies on a minimalistic hardware description
  language (HDL) written in YAML.
* `PyHyCon` is an interface to a Model-1 Hybrid Controller in order to
  run a program, steer the operation and gain output data.
  
> :information_source: **Please read the docs**:
> As a starting point, see `docs/` or `make docs`. You can find
> the generated docs at **https://www.anabrid.dev/pyanalog/docs/dirhtml/**
>
> We used to serve them from https://pyanalog.readthedocs.io/ but 
> abandoned ReadTheDocs due to missing features.

## Directory structure

```
.
├── dda                 - The PyDDA module
├── doc                 - holding the Sphinx-based documentation
├── Dockerfile          - primarily for the CI and testing
├── examples            - a large number of applications and examples
├── fpaa                - The PyFPAA module
├── hycon               - The PyHyCon module
├── LICENSE.ANABRID     - Part of the License texts, see below for more information
├── LICENSE.DE          - Part of the License texts, see below for more information
├── LICENSE.GPL3        - Part of the License texts, see below for more information
├── LICENSE.py          - Generator forthe License texts
├── Makefile            - Not really an entry point, but see below
├── misc                - Old files, such as Mathematica notebooks or Perl codes
├── README.md           - This very file
├── requirements.txt    - A dependencies file for pip, see also doc/installation.rst
├── setup.py            - A python installer, see also doc/installation.rst
└── tests               - Unit tests (which also can be useful examples)
```

## About the Makefile

PyAnalog is basically a collection of scripts, so there is no such thing as 
``make build``. However, you can try ``make install``, which will basically
execute ``setup.py``. Read [doc/installation.rst](doc/installation.rst)
for further details.

### The shortest quick start (of PyDDA)

This directory holds the package root directory (where `setup.py` lives)
of the PyDDA package. This is mostly a pure Python3 package with no
dependencies.

If you are lazy, you can start using PyDDA right from here:

```
$ git clone git@github.com:anabrid/pyanalog.git
$ cd pyanalog
$ python3
>>> from dda import *
>>> s = BreveState()
>>> s.x = Symbol("int", "x", 0.02, 0)
>>> print(s)
BreveState({'x': int(x, 0.02, 0)})
```

Please read [doc/installation.rst](doc/installation.rst) for further instructions on how to use the
package. It contains also instructions how to install PyAnalog properly.
Run `make` to see the various formats the documentation can be generated in.

## About the License

Basically, this code is *Open Sourced* by the *GPLv3*. However, we have a different license model
for commercial use. In order to stay safe regarding liability questions, we also refer to the 
[LICENSE.DE](LICENSE.DE) for legal issues relevant to Germany. Here is the full license
text which typically prepends any file within this repository:

```
ANABRID_BEGIN_LICENSE:GPL
Commercial License Usage
Licensees holding valid commercial anabrid licenses may use this file in
accordance with the commercial license agreement provided with the
Software or, alternatively, in accordance with the terms contained in
a written agreement between you and Anabrid GmbH. For licensing terms
and conditions see https://www.anabrid.com/licensing. For further
information use the contact form at https://www.anabrid.com/contact.

GNU General Public License Usage
Alternatively, this file may be used under the terms of the GNU 
General Public License version 3 as published by the Free Software
Foundation and appearing in the file LICENSE.GPL3 included in the
packaging of this file. Please review the following information to
ensure the GNU General Public License version 3 requirements
will be met: https://www.gnu.org/licenses/gpl-3.0.html.
For Germany, additional rules exist. Please consult /LICENSE.DE
for further agreements.
ANABRID_END_LICENSE
```

## Further questions?

This code was primarily written by https://github.com/svenk within the years 2020/21.
If you have any questions, you should drop him a mail or use the Github tools (such as opening an Issue).

Stay analog!

