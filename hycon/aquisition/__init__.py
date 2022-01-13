#
# Copyright (c) 2020 anabrid GmbH
# Contact: https://www.anabrid.com/licensing/
#
# This file is part of the HyCon module of the PyAnalog toolkit.
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
# For Germany, additional rules exist. Please consult /LICENSE.DE
# for further agreements.
# ANABRID_END_LICENSE
#

"""
The :mod:`hycon.aquisition` package collects various codes related to *data aquisition*.
Currently, we have a number of pythonic analog2digital data auqisition
routines:

  - The Hybrid Controller uC itself offers methods such as
    :meth:`hycon.HyCon.HyCon.read_ro_group` and similar. The aquisition
    is high precision (16bit) but quite limited in time, given the small
    memory of the uC which is used for store the full aquisition before
    a transfer is possible (no streaming implemented).
  - DSOs (digital storage oscilloscopes) can be used for high quality
    and industry standard data aquisition. A particular python example is
    provided in the :class:`siglent_scpi.siglent` code.
    These devices are typically also limited in aquisition time, which is
    naturally mapped to the display. Furthermore, these devices are always
    very limited in the number of analog channels, and devices with
    many channels are expensive.
  - Custom Data loggers provide maximum flexibilty, given the large amount
    of channels implementable with cheap microcontrollers
    such as the `Teensy <https://www.pjrc.com/teensy/>`_. However, these
    cheap uCs typically only have an average resolution of 10bit.
    A particular
    example is given at https://github.com/anabrid/TeensyLogger
    (see also https://the-analog-thing.org/wiki/Teensy).

When it comes to classical analog computing, one would like to optimize
the aquisition for high resolution (16bit), many channels (as many as possible).
What is not so important is the sampling rate, since the cutoff frequency of
the discrete circuits is rather low (at the order of MHz).  
"""

# Please see ../../doc/ for documentation.

from .siglent_scpi import siglent
