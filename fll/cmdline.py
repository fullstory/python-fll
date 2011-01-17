"""
This is the fll.cmdline module, it provides a function for parsing supported
command line options.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

import argparse


class AddAptSource(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        label = values.pop(0)
        if label.startswith('label='):
            label = label.partition('=')[2]
        else:
            msg = 'first argument must be label=<LABEL>'
            raise argparse.ArgumentError(self, msg)

        source = {'description': '%s package repository' % label,
                  'suites': ['sid'],
                  'components': ['main']}

        for value in values:
            k, _, v = value.partition('=')
            if k in ['suites', 'components']:
                source[k] = v.split(',')
            else:
                source[k] = v

        if 'uri' not in source:
            msg = 'missing required argument: uri=<URI>'
            raise argparse.ArgumentError(self, msg)

        setattr(namespace, 'apt_sources_%s' % label, source)


class SetEnvConfig(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        conf = {}

        for value in values:
            k, _, v = value.partition('=')
            conf[k] = v

        setattr(namespace, self.dest, conf)


def cmdline():
    desc="""\
Live GNU/Linux media building utility.

fll builds a flexible operating system, based on Debian GNU/Linux, which is
able to boot into a functional environment on a wide variety of hardware.
This software prepares a Debian chroot in a compressed filesystem container
for deployment onto bootable removable media such as CD/DVD, usb drive or
memory card.

Examples:
    Select AARNET mirror:
    $ fll --mirror=http://mirror.aarnet.edu.au/debian

    Build in /var/tmp directory:
    $ fll --dir=/var/tmp

    Build multiple chroot filesystems and include contrib and non-free Debian
    archive components:
    $ fll --archs amd64 i386 --components main contrib non-free

    Add aptosid package repository to chroot's apt sources:
    $ fll --apt-source label=aptosid uri=http://aptosid.com/debian/ \\
          components=main,fix.main keyring=aptosid-archive-keyring
"""
    formatter = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(description=desc, prog='fll',
                                formatter_class=formatter)

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

    b = p.add_argument_group(title='build system related arguments')
    b.add_argument('--config', '-C',
                   metavar='<FILE>',
                   type=argparse.FileType('r'),
                   help="""\
Alternate configuration file.
Default: /etc/fll/fll.conf""")

    b.add_argument('--dump', '-D',
                   metavar='<FILE>',
                   type=argparse.FileType('w'),
                   help="""\
Dump configuration object to file and exit.""")

    b.add_argument('--dir', '-d',
                   metavar='<DIR>',
                   help="""\
Build directory for staging chroot filesystem(s) and resulting output.
A very large amount of free space is required.
Default: current working directory""")

    b.add_argument('--uid', '-u',
                   type=int,
                   metavar='<UID>',
                   help="""\
Set user ownership of output files to specified UID.""")

    b.add_argument('--gid', '-g',
                   type=int,
                   metavar='<GID>',
                   help="""\
Set group ownership of output files to specified GID.""")

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

    d.add_argument('--src', '-S',
                   action='store_true',
                   help="""\
Fetch and build source archive of software included in chroot filesystem(s).
Default: False""")

    a = p.add_argument_group(title='apt related arguments')

    a.add_argument('--apt-conf',
                   metavar='<KEYWORD=VALUE>',
                   nargs='+',
                   action=SetEnvConfig,
                   help="""\
Set apt configuration. Each argument is a keyword=value pair.""")

    a.add_argument('--apt-source',
                   metavar='<SOURCE>',
                   nargs='+',
                   action=AddAptSource,
                   help="""\
Add an apt source to the configuration. Arguments to this option are
keyword=value pairs using the same keywords as specified in [apt][[sources]]
section of fll.conf. This option may be used more than once to add multiple
apt repository configurations to the build.""")

    a.add_argument('--apt-key-disable',
                   action='store_true',
                   help="""\
Do not do trust verification of apt's sources.""")

    a.add_argument('--apt-key-server',
                   metavar='<KEYSERVER>',
                   help="""\
GPG Keyserver to fetch pubkeys from when securing apt.
Default: wwwkeys.eu.pgp.net""")

    a.add_argument('--apt-verbose',
                   action='store_true',
                   help="""\
Select verbose mode for apt actions, overriding the global verbosity mode.
""")

    a.add_argument('--apt-debug',
                   action='store_true',
                   help="""\
Select debug mode for apt actions, overriding the global verbosity mode.
""")

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

    c.add_argument('--chroot-preserve', '-P',
                   action='store_true',
                   help="""\
Preserve chroot filesystem after completion.
Default: False""")

    c.add_argument('--chroot-verbose',
                   action='store_true',
                   help="""\
Select verbose mode for chroot actions, overriding the global verbosity mode.
""")

    c.add_argument('--chroot-debug',
                   action='store_true',
                   help="""\
Select debug mode for chroot actions, overriding the global verbosity mode.
""")

    e = p.add_argument_group(title='environment related arguments')

    e.add_argument('--environment',
                   metavar='<KEYWORD=VALUE>',
                   nargs='+',
                   action=SetEnvConfig,
                   help="""\
Set environment configuration. Each argument is a keyword=value pair.""")

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
    p.add_argument('--config', '-C', type=argparse.FileType('r'))
    args, _ = p.parse_known_args()

    return args.config

def get_dump_file():
    """Parse sys.argv for --dump argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--dump', '-D', type=argparse.FileType('w'))
    args, _ = p.parse_known_args()

    return args.dump
