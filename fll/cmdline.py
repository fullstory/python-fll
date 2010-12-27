"""
This is the fll.cmdline module, it provides a function for parsing supported
command line options.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import optparse
import os


def cmdline():
    usage='Usage: %prog --config=<CONF> [<OPTIONS>]'

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

    p = optparse.OptionParser(usage=usage, description=desc, prog='fll')

    p.add_option('-b', '--build-dir', dest='build_dir', action='store',
                 type='string', metavar='<DIR>', default=os.getcwd(),
                 help="""\
Build directory for staging chroot(s), binary and source output. A large
amount of free space is required. Defaults to the current working
directory.""")

    p.add_option('-c', '--config', dest='config', action='store', type='string',
                 metavar='<CONF>', default=None, help="""\
Configuration file for build. This option is mandatory.""")

    p.add_option('-s', '--fetch-source', dest='fetch_source',
                 action='store_true', default=False, help="""\
Fetch source packages for all packages installed in the chroot and organise
them in an archive. Default: %default""")

    p.add_option('--debian-frontend', dest='debian_frontend', action='store',
                 type='string', metavar='<FRONTEND>', default='noninteractive',
                 help="""\
Sets the DEBIAN_FRONTEND environment variable, used by debconf, which dictates
how package configuration questions are handled. Default: %default.""")

    p.add_option('--debian-priority', dest='debian_priority', action='store',
                 type='string', metavar='<PRIORITY>', default='critical',
                 help="""\
Sets the DEBIAN_PRIORITY environment variable, used by debconf, which dictates
what package configuration questions are shown. Default: %default.""")

    p.add_option('--execute', dest='execute', action='store', type='string',
                 metavar='<SCRIPT>', default='/usr/share/fll/fullstory.py',
                 help="""\
Set alternative script for fll shell wrapper to execute. This option should
never be required unless you are running fll from its source tree.
Default: %default.""")

    p.add_option('--ftp-proxy', dest='ftp_proxy', action='store',
                 type='string', metavar='<PROXY>', default=None,
                 help="""\
Sets the ftp_proxy environment variable. Default: %default.""")

    p.add_option('--http-proxy', dest='http_proxy', action='store',
                 type='string', metavar='<PROXY>', default=None,
                 help="""\
Sets the http_proxy environment variable. Default: %default.""")

    return p
