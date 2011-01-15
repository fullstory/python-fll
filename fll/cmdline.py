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

    p.add_argument('--config', '-C',
                   metavar='<FILE>',
                   type=file,
                   help="""\
Alternate configuration file.
Default: /etc/fll/fll.conf""")

    p.add_argument('--dir', '-d',
                   metavar='<DIR>',
                   help="""\
Build directory for staging chroot filesystem(s) and resulting output.
A very large amount of free space is required.
Default: current working directory""")

    p.add_argument('--uid', '-u',
                   type=int,
                   metavar='<UID>',
                   help="""\
Set user ownership of output files to specified UID.""")

    p.add_argument('--gid', '-g',
                   type=int,
                   metavar='<GID>',
                   help="""\
Set group ownership of output files to specified GID.""")

    p.add_argument('--dry-run', '-n',
                   dest='dryrun',
                   action='store_true',
                   help="""\
Dry run mode. Do not perform time consuming processes.""")

    m = p.add_mutually_exclusive_group()
    m.add_argument('--verbosity',
                   metavar='<MODE>', 
                   choices=['quiet', 'verbose', 'debug'],
                   help=argparse.SUPPRESS)

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

    d = p.add_argument_group(title='distribution related arguments')

    d.add_argument('--archs', '-a',
                   metavar='<ARCH>',
                   nargs='+',
                   choices=['amd64', 'i386'],
                   help="""\
Architecture of chroot filesystem(s) to build. Multiple architectures
can be specified separarted by whitespace.
Default: host architecture""")

    d.add_argument('--suites', '-s',
                   dest='apt_sources_debian_suites',
                   metavar='<SUITE>',
                   nargs='+',
                   choices=['squeeze', 'testing', 'sid', 'unstable',
                            'experimental'],
                   help="""\
Distribution suite or codename (e.g. testing, unstable, sid).
Default: sid""")

    d.add_argument('--mirror', '-m',
                   metavar='<URI>',
                   help="""\
Distribution mirror.
Default: http://cdn.debian.net/debian/""")

    d.add_argument('--components', '-c',
                   dest='apt_sources_debian_components',
                   metavar='<COMPONENT>',
                   nargs='+',
                   choices=['main', 'contrib', 'non-free'],
                   help="""\
Distribution components to be used.
Default: main""")

    a = p.add_argument_group(title='apt related arguments')

    a.add_argument('--apt-src',
                   action='store_true',
                   help="""\
Fetch and build source archive of software included in chroot filesystem(s).
Default: False""")

    a.add_argument('--apt-key-disable',
                   action='store_true',
                   help="""\
Do not do trust verification of apt's sources.""")

    a.add_argument('--apt-key-server',
                   metavar='<KEYSERVER>',
                   help="""\
GPG Keyserver to fetch pubkeys from when securing apt.
Default: wwwkeys.eu.pgp.net""")

    c = p.add_argument_group(title='chroot related arguments')

    c.add_argument('--bootstrap-flavour',
                   dest='chroot_bootstrap_flavour',
                   metavar='<FLAVOUR>',
                   choices=['minimal', 'build', 'standard'],
                   help="""\
Bootstrap chroot flavour. Choices: %(choices)s.
Default: minimal""")

    c.add_argument('--bootstrap-suite',
                   dest='chroot_bootstrap_suite',
                   metavar='<SUITE>',
                   help="""\
Bootstrap suite.
Default: sid""")

    c.add_argument('--bootstrap-utility',
                   dest='chroot_bootstrap_utility',
                   metavar='<UTILITY>',
                   choices=['cdebootstrap', 'debootstrap'],
                   help="""\
Bootstrap utility to prepare chroot. Choices: %(choices)s.
Default: cdebootstrap""")

    c.add_argument('--bootstrap-uri',
                   dest='chroot_bootstrap_uri',
                   metavar='<URI>',
                   help="""\
Bootstrap mirror.
Default: http://cdn.debian.net/debian/""")

    c.add_argument('--preserve', '-P',
                   dest='chroot_preserve',
                   action='store_true',
                   help="""\
Preserve chroot filesystem after completion.
Default: False""")

    n = p.add_argument_group(title='network related arguments')

    n.add_argument('--ftp-proxy',
                   dest='network_ftp_proxy',
                   metavar='<PROXY>',
                   help="""\
Sets the ftp_proxy environment variable and apt's Acquire::http::Proxy
configuration item.""")

    n.add_argument('--http-proxy',
                   dest='network_http_proxy',
                   metavar='<PROXY>',
                   help="""\
Sets the http_proxy environment variable and apt's Acquire::ftp::Proxy
configuration item.""")

    return p

def get_config_file():
    """Parse sys.argv for --config argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--config', '-C', type=file)
    args, _ = p.parse_known_args()

    return args.config
