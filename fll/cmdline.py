"""
This is the fll.cmdline module, it provides a function for parsing supported
command line options.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import argparse


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

    p.add_argument('--architecture', '-a', metavar='<ARCH>', action='append',
                   help="""\
Architecture of chroot to build. May be specified multiple times.
Default: host architecture""")

    p.add_argument('--build-dir', '-b', metavar='<DIR>', help="""\
Build directory for staging chroot(s), binary and source output. A large
amount of free space is required.
Default: current working directory""")

    p.add_argument('--config-file', '-c', type=file, metavar='<CONFIG>', 
                   help="""\
Configuration file for build. Default: /etc/fll/fll.conf""")

    p.add_argument('--dryrun', '-D', action='store_true', help="""\
Dry run mode. Do not perform time consuming processes.
Default: %(default)s""")

    p.add_argument('--ftp-proxy', '-F', metavar='<PROXY>', help="""\
Sets the ftp_proxy environment variable and apt's Acquire::http::Proxy
configuration item.""")

    p.add_argument('--http-proxy', '-H', metavar='<PROXY>', help="""\
Sets the http_proxy environment variable and apt's Acquire::ftp::Proxy
configuration item.""")

    p.add_argument('--mirror', '-m', metavar='<URI>', help="""\
Debian mirror to be used. Default: http://cdn.debian.net/debian/""")

    p.add_argument('--preserve-chroot', '-P', action='store_true', help="""\
Preserve chroot filesystem after completion. Default: %(default)s""")

    p.add_argument('--source', '-s', action='store_true', help="""\
Fetch and build source archive of software included in chroot filesystems.
Default: %(default)s""")
    
    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--verbosity', metavar='<MODE>', 
                       choices=['quiet', 'verbose', 'debug'], help="""\
Select verbosity mode of quiet, verbose or debug. Default: quiet""")

    modes.add_argument('--quiet', '-q', action='store_true', default=False,
                       help="""\
Select quiet verbosity mode.""")
    modes.add_argument('--verbose', '-v', action='store_true', default=False,
                       help="""\
Select verbose verbosity mode.""")
    modes.add_argument('--debug', '-d', action='store_true', default=False,
                       help="""\
Select debug verbosity mode.""")

    return p
