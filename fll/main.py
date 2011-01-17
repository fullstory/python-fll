"""
This is the fll.main module, it links all the other fll modules together.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from fll.aptlib import AptLib, AptLibError
from fll.chroot import Chroot, ChrootError
from fll.config import Config, ConfigError
from fll.distro import Distro, DistroError

import os
import sys

def error(msg):
    print >>sys.stderr, 'E: fll - %s' % msg
    sys.exit(1)

def main():
    try:
        conf = Config()
    except (ConfigError, IOError), e:
        error(e)

    for arch in conf.config['archs']:
        rootdir = os.path.join(conf.config['dir'], arch)

        try:
            with Chroot(rootdir=rootdir, architecture=arch,
                        config=conf.config['chroot']) as chroot:
                chroot.bootstrap()
                chroot.init()

                apt = AptLib(chroot=chroot, config=conf.config['apt'])
                apt.init()

                apt.install(['man-db'], commit=False)
                for change in apt.changes():
                    print change
                apt.commit()

                apt.deinit()
                chroot.deinit()
        except (AptLibError, ChrootError), e:
            error(e)
