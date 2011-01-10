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
    formatter = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description=desc, prog='fll',
                                formatter_class=formatter)

    p.add_argument('--src', '-S',
                   dest='apt_src',
                   action='store_true',
                   help="""\
Fetch and build source archive of software included in chroot filesystem(s).
Default: False""")

    p.add_argument('--noaptkey', '-X',
                   dest='apt_key_disable',
                   action='store_true',
                   help="""\
Do not do trust verification of apt's sources.""")

    p.add_argument('--keyserver', '-K',
                   dest='apt_key_server',
                   metavar='<KEYSERVER>',
                   help="""\
GPG Keyserver to fetch pubkeys from when securing apt.
Default: wwwkeys.eu.pgp.net""")

    p.add_argument('--archs', '-a',
                   metavar='<ARCH>',
                   nargs='+',
                   help="""\
Architecture(s) of chroot filesystem(s) to build. Multiple architectures
can be specified separarted by whitespace. Default: host architecture""")

    p.add_argument('--build', '--dir', '-b',
                   metavar='<DIR>',
                   help="""\
Build directory for staging chroot filesystem(s) and resulting output.
A very large amount of free space is required.
Default: current working directory""")

    p.add_argument('--preserve', '-P',
                   dest='chroot_preserve',
                   action='store_true',
                   help="""\
Preserve chroot filesystem after completion. Default: %(default)s""")

    p.add_argument('--bootstrapper', '-B',
                   dest='chroot_bootstrap_utility',
                   metavar='<UTIL>',
                   choices=['cdebootstrap', 'debootstrap'],
                   help="""\
Bootstrap utility to prepare chroot. Choices: %(choices)s""")

    p.add_argument('--flavour', '-F',
                   dest='chroot_bootstrap_flavour',
                   metavar='<FLAV>',
                   choices=['minimal', 'build', 'standard'],
                   help="""\
Debian chroot flavour. Default: minimal""")

    p.add_argument('--config', '--file', '-c',
                   metavar='<FILE>',
                   type=file,
                   help="""\
Configuration file. Default: /etc/fll/fll.conf""")

    p.add_argument('--dryrun', '--dry-run', '-d',
                   action='store_true',
                   help="""\
Dry run mode. Do not perform time consuming processes.
Default: %(default)s""")

    p.add_argument('--ftp', '--ftp-proxy',
                   metavar='<PROXY>',
                   help="""\
Sets the ftp_proxy environment variable and apt's Acquire::http::Proxy
configuration item.""")

    p.add_argument('--http', '--http-proxy',
                   metavar='<PROXY>',
                   help="""\
Sets the http_proxy environment variable and apt's Acquire::ftp::Proxy
configuration item.""")

    p.add_argument('--mirror', '--uri', '-m',
                   metavar='<URI>',
                   help="""\
Debian mirror to be used. Default: http://cdn.debian.net/debian/""")

    p.add_argument('--codename', '--suite', '-C',
                   metavar='<SUITE>',
                   help="""\
Debian suite or codename (e.g. testing, unstable, sid).
Default: sid""")

    m = p.add_mutually_exclusive_group()
    m.add_argument('--verbosity',
                   metavar='<MODE>', 
                   choices=['quiet', 'verbose', 'debug'],
                   help="""\
Select verbosity mode. Choices: %(choices)s""")

    m.add_argument('--quiet', '-q',
                   action='store_const',
                   dest='verbosity',
                   const='quiet',
                   help="""\
Select quiet verbosity mode.""")

    m.add_argument('--verbose', '-v',
                   action='store_const',
                   dest='verbosity',
                   const='verbose',
                   help="""\
Select verbose verbosity mode.""")

    m.add_argument('--debug', '-x',
                   action='store_const',
                   dest='verbosity',
                   const='debug',
                   help="""\
Select debug verbosity mode.""")

    return p

def get_config_file():
    """Parse sys.argv for --config argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--config', '-c', type=file)
    args, _ = p.parse_known_args()

    return args.config
