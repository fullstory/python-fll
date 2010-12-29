"""
This is the fll.cmdline module, it provides a function for parsing supported
command line options.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import argparse
import os


def cmdline():
    desc="""\
Live GNU/Linux media building utility.

fll builds a flexible operating system, based on Debian GNU/Linux, which is
able to boot into a functional environment on a wide variety of hardware.
This software prepares a Debian chroot in a compressed filesystem container
for deployment onto bootable removable media such as CD/DVD, usb drive or
memory card.

Features:
    * simple to configure and use
    * flexible package modules
    * debconf pre-seeding for package configuration
    * uses python-apt interface for package management
"""

    p = argparse.ArgumentParser(description=desc, prog='fll',
            formatter_class=argparse.RawDescriptionHelpFormatter)

    p.add_argument('--build-dir', '-b', default=os.getcwd(), metavar='<DIR>',
                   help="""\
Build directory for staging chroot(s), binary and source output. A large
amount of free space is required. Defaults to the current working
directory.""")

    p.add_argument('--config', '-c', type=file, metavar='<CONFIG>', 
                   required=True, help="""\
Configuration file for build. This option is mandatory.""")

    p.add_argument('--debian-frontend', default='noninteractive',
                   metavar='<FRONTEND>', help="""\
Sets the DEBIAN_FRONTEND environment variable, used by debconf, which dictates
how package configuration questions are handled. Default: %(default)s.""")

    p.add_argument('--debian-priority', default='critical',
                   metavar='<PRIORITY>', help="""\
Sets the DEBIAN_PRIORITY environment variable, used by debconf, which dictates
what package configuration questions are shown. Default: %(default)s.""")

    p.add_argument('--execute', default='/usr/share/fll/fullstory.py',
                   metavar='<PROGRAM>', help="""\
Set alternative script for fll shell wrapper to execute. This option should
never be required unless you are running fll from its source tree.
Default: %(default)s.""")

    p.add_argument('--fetch-src', '-f', action='store_true', default=False,
                   help="""\
Fetch source packages for all packages installed in the chroot and organise
them in an archive. Default: %(default)s""")

    p.add_argument('--ftp-proxy', metavar='<PROXY>', help="""\
Sets the ftp_proxy environment variable.""")

    p.add_argument('--http-proxy', metavar='<PROXY>', help="""\
Sets the http_proxy environment variable.""")

    return p
