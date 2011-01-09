"""
This is the fll.cmdline module, it provides a function for parsing supported
command line options.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import fll.misc
import argparse
import os


class _RealPath(argparse.Action):
    """Custom action to store realpath of file/dir values."""
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, os.path.realpath(value))


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

    p.add_argument('--apt-fetch-src', '-s', action='store_true', help="""\
Fetch and build source archive of software included in chroot filesystem(s).
Default: False""")

    p.add_argument('--apt-insecure', '-i', action='store_true', help="""\
Do not do trust verification of apt's sources.""")

    p.add_argument('--apt-keyserver', '-K', metavar='<KEYSERVER>', help="""\
GPG Keyserver to fetch pubkeys from when securing apt.
Default: wwwkeys.eu.pgp.net""")

    arch = fll.misc.cmd('dpkg --print-architecture', pipe=True, silent=True)
    p.add_argument('--architecture', '-a', metavar='<ARCH>', nargs='+',
                   default = [arch.strip()], help="""\
Architecture(s) of chroot filesystem(s) to build. Multiple architectures
can be specified separarted by whitespace. Default: host architecture""")

    p.add_argument('--build-dir', '-b', metavar='<DIR>', action=_RealPath,
                   default = os.getcwd(), help="""\
Build directory for staging chroot filesystem(s) and resulting output.
A very large amount of free space is required.
Default: current working directory""")

    p.add_argument('--chroot-preserve', '-P', action='store_true', help="""\
Preserve chroot filesystem after completion. Default: %(default)s""")

    p.add_argument('--config-file', '-c', type=file, metavar='<CONFIG>',
                   help="""\
Configuration file. Default: /etc/fll/fll.conf""")

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

    modes = p.add_mutually_exclusive_group()
    modes.add_argument('--verbosity', metavar='<MODE>', 
                       choices=['quiet', 'verbose', 'debug'],
                       default='quiet', help="""\
Select verbosity mode of quiet, verbose or debug. Default: %(default)s""")

    modes.add_argument('--quiet', '-q', action='store_const',
                       dest='verbosity', const='quiet', help="""\
Select quiet verbosity mode.""")

    modes.add_argument('--verbose', '-v', action='store_const',
                       dest='verbosity', const='verbose', help="""\
Select verbose verbosity mode.""")

    modes.add_argument('--debug', '-d', action='store_const',
                       dest='verbosity', const='debug', help="""\
Select debug verbosity mode.""")

    return p

def get_config_file():
    """Parse sys.argv for --config argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--config-file', '-c', type=file, metavar='<CONFIG>')
    args, _ = p.parse_known_args()

    return args.config_file
