"""
This is the fll.main module, it links all the other fll modules together.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from fll.aptlib import AptLib, AptLibError, AptLibProgress
from fll.chroot import Chroot, ChrootError
from fll.config import Config, ConfigError
import fll.cmdline

import os
import sys


def main():
    args = fll.cmdline.cmdline().parse_args()
    conf = Config(config_file=args.config, cmdline=args)
    conf.set_environment()
