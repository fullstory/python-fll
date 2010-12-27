"""
This is the fll.main module, it links all the other fll modules together.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from fll.aptlib import AptLib, AptLibError, AptLibProgress
from fll.chroot import Chroot, ChrootError
from fll.cmdline import cmdline

import os
import sys


def main():
    opts, args = cmdline().parse_args()
