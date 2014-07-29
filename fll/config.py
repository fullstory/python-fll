"""
This is the fll.config module, it provides a class for abstracting the
fll configuration file and command line arguments.

Author:    Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from configobj import ConfigObj, ConfigObjError, \
                      flatten_errors, get_extra_values
from validate import Validator

import argparse
import os
import sys

import fll.misc


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
                   nargs='?',
                   type=argparse.FileType('w'),
                   const=sys.stdout,
                   help="""\
Dump configuration object and exit. A file to output to may be given as
an argument, otherwise the configuration is dumped to stdout.""")

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
                   help="""\
Architecture of chroot filesystem(s) to build. Multiple architectures
can be specified separarted by whitespace.
Default: host architecture""")

    d.add_argument('--suites', '-s',
                   dest='apt_sources_debian_suites',
                   metavar='<SUITE>',
                   nargs='+',
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
                   dest='apt_src',
                   action='store_true',
                   help="""\
Fetch and build source archive of software included in chroot filesystem(s).
""")

    d.add_argument('--distro',
                   metavar='<KEYWORD=VALUE>',
                   nargs='+',
                   action=SetEnvConfig,
                   help="""\
Set distro defaults configuration. Each argument is a keyword=value pair.""")

    a = p.add_argument_group(title='apt related arguments')

    a.add_argument('--apt-conf',
                   metavar='<KEYWORD=VALUE>',
                   nargs='+',
                   action=SetEnvConfig,
                   help="""\
Set apt configuration. Each argument is a keyword=value pair.""")

    a.add_argument('--apt-source',
                   metavar='<KEYWORD=VALUE>',
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

    a.add_argument('--apt-quiet',
                   action='store_true',
                   help="""\
Select quiet mode for apt actions, overriding the global verbosity mode.
""")

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

    pm = p.add_argument_group(title='package module related arguments')

    pm.add_argument('--profile-name',
                    dest='profile_name',
                    metavar='<PROFILE>',
                    help="""\
Name of package module to base system profile upon.""")

    pm.add_argument('--profile-dir',
                    dest='profile_dir',
                    metavar='<DIR>',
                    help="""\
Package module directory path name.""")

    pm.add_argument('--profile-packages',
                    dest='profile_packages',
                    nargs='+',
                    metavar='<PACKAGES>',
                    help="""\
List of package names to append to package profile.""")

    c = p.add_argument_group(title='chroot related arguments')

    c.add_argument('--chroot-flavour',
                   dest='chroot_bootstrap_flavour',
                   metavar='<FLAVOUR>',
                   choices=['minimal', 'build', 'standard'],
                   help="""\
Chroot flavour. Choices: %(choices)s.
Default: minimal""")

    c.add_argument('--chroot-suite',
                   dest='chroot_bootstrap_suite',
                   metavar='<SUITE>',
                   help="""\
Chroot suite or codename (e.g. testing, unstable, sid).
Default: sid""")

    c.add_argument('--chroot-utility',
                   dest='chroot_bootstrap_utility',
                   metavar='<UTILITY>',
                   choices=['cdebootstrap', 'debootstrap'],
                   help="""\
Bootstrap utility to prepare chroot. Choices: %(choices)s.
Default: cdebootstrap""")

    c.add_argument('--chroot-uri',
                   dest='chroot_bootstrap_uri',
                   metavar='<URI>',
                   help="""\
Bootstrap mirror.
Default: http://cdn.debian.net/debian/""")

    c.add_argument('--chroot-include',
                   dest='chroot_bootstrap_include',
                   metavar='<PKGS>',
                   help="""\
Comma delimited list of packages to include during bootstrap.
""")

    c.add_argument('--chroot-exclude',
                   dest='chroot_bootstrap_exclude',
                   metavar='<PKGS>',
                   help="""\
Comma delimited list of packages to exclude during bootstrap.
""")

    c.add_argument('--chroot-preserve', '-P',
                   action='store_true',
                   help="""\
Preserve chroot filesystem after completion.
Default: False""")

    c.add_argument('--chroot-quiet',
                   action='store_true',
                   help="""\
Select quiet mode for chroot actions, overriding the global verbosity mode.
""")

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

    c.add_argument('--hostname',
                   dest='chroot_hostname',
                   metavar='<HOSTNAME>',
                   help="""\
Hostname to assign to the chroot.
Default: chroot""")

    f = p.add_argument_group(title='filesystem related arguments')

    f.add_argument('--compression',
                   dest='fscomp_compression',
                   metavar='<COMP>',
                   choices=['squashfs','tar','none'],
                   help="""\
Select compression type. Choices: %(choices)s.
Default: squashfs""")

    f.add_argument('--squashfs-compressor',
                   dest='fscomp_squashfs_compressor',
                   metavar='<COMPRESSOR>',
                   choices=['gzip', 'lzo', 'xz'],
                   help="""\
Squashfs compression type. Choices: %(choices)s.
Default: gzip""")

    f.add_argument('--tar-compressor',
                   dest='fscomp_tar_compressor',
                   metavar='<COMPRESSOR>',
                   choices=['gz', 'bz', 'pz', 'xz'],
                   help="""\
Tar compression type. Choices: %(choices)s.
Default: gzip""")

    f.add_argument('--fscomp-quiet',
                   action='store_true',
                   help="""\
Select quiet mode for fscomp actions, overriding the global verbosity mode.
""")

    f.add_argument('--fscomp-verbose',
                   action='store_true',
                   help="""\
Select verbose mode for fscomp actions, overriding the global verbosity mode.
""")

    f.add_argument('--fscomp-debug',
                   action='store_true',
                   help="""\
Select debug mode for fscomp actions, overriding the global verbosity mode.
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


def get_config_file():
    """Parse sys.argv for --config argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--config', '-C', type=argparse.FileType('r'))
    args, _ = p.parse_known_args()

    return args.config


def get_dump_file():
    """Parse sys.argv for --dump argument and return its value."""
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--dump', '-D', type=argparse.FileType('w'), nargs='?',
                   const=sys.stdout)
    args, _ = p.parse_known_args()

    return args.dump


class ConfigError(Exception):
    """
    An Error class for use by Config.
    """
    pass


class Config(object):
    """
    A class for abstracting the fll configuration file.
    """
    def __init__(self):
        self.config_file = get_config_file()
        if self.config_file is None:
            self.config_file = file(os.devnull)

        if os.path.isfile('data/fll.conf.spec'):
            self.config_spec = file(os.path.realpath('data/fll.conf.spec'))
        else:
            self.config_spec = file('/usr/share/fll/data/fll.conf.spec')

        self.config = ConfigObj(self.config_file, configspec=self.config_spec,
                                interpolation='template')

        self._process_cmdline()
        self._validate_config()
        self._debug_configobj()
        self._propogate_modes()
        self._config_defaults()
        self._set_environment()

    def _validate_config(self):
        """Check for errors in the configuration file. Bail out if required
        sections/values are missing, or if extra sections/values are
        present."""
        result = self.config.validate(Validator(), preserve_errors=True,
                                      copy=True)
        error_msgs = []

        for sections, name in get_extra_values(self.config):
            the_section = self.config
            try:
                for section in sections:
                    the_section = self.config[section]
            except KeyError:
                continue

            the_value = the_section[name]

            section_or_value = 'value'
            if isinstance(the_value, dict):
                section_or_value = 'section'

            section_string = ', '.join(sections) or 'top level'

            msg = 'E: extra %s entry in %s section: %r' % \
                  (section_or_value, section_string, name)
            error_msgs.append(msg)

        for entry in flatten_errors(self.config, result):
            section_list, key, error = entry
            if key is None:
                section_list.append('section missing')
            else:
                section_list.append(key)

            if error == False:
                error = 'value or section missing'

            msg = 'E: config%s: %s' % \
                  (''.join(["['%s']" % s for s in section_list]), error)
            error_msgs.append(msg)

        if error_msgs:
            error_msgs.insert(0, 'config file failed validation: %s' %
                              self.config_file.name)
            raise ConfigError('\n'.join(error_msgs))

    def _process_cmdline(self):
        """Parse command line arguments and merge them with the configuration
        file object. Command line arguments are trumps. They are stored in a
        Namespace object which are mapped to the configuration file object
        like so:
        
        For each name in the Namespace object we split by underscore, and each
        segment then represents a config file section key. eg:

            args.Namespace('apt_sources_debian_uri') = value
            |
            `-> config['apt']['sources']['debian']['uri'] = value
        """
        args = cmdline().parse_args()

        debug = args.verbosity == 'debug'

        for key, value in args.__dict__.iteritems():
            if value in [None, False]:
                continue
            if isinstance(value, file):
                continue

            keys = key.split('_')

            config = {keys.pop(-1): value}
            for k in reversed(keys):
                config = {k: config}

            fll.misc.debug(debug, key, config)
            self.config.merge(config)

        fll.misc.debug(debug, 'config', self.config.dict())

    def _config_defaults(self):
        """Set some defaults which are not able to be set in fll.conf.spec."""
        if not self.config['archs']:
            arch = fll.misc.cmd('dpkg --print-architecture', pipe=True,
                                silent=True)
            self.config['archs'] = [arch.strip()]

        self.config['dir'] = os.path.realpath(self.config['dir'])

    def _propogate_modes(self):
        """Propogate global verbosity mode to config sections. Do not
        propogate to sections which have independently configured verbosity
        mode."""
        mode = self.config['verbosity']
        other_modes = set(['quiet', 'verbose', 'debug'])
        other_modes.discard(mode)

        for section in self.config.keys():
            if isinstance(self.config[section], dict):
                try:
                    for m in other_modes:
                        if self.config[section][m] is True:
                            break
                    else:
                        self.config[section][mode] = True
                except KeyError:
                    pass

    def _debug_configobj(self):
        """Dump configuration object to file."""
        dump_file = get_dump_file()
        if dump_file is not None:
            self.config.write(dump_file)
            sys.exit(0)

    def _set_environment(self):
        """Set environment variables as per 'environment' config settings.
        Propogate http/ftp proxy settings to apt configuration."""
        for k, v in self.config['environment'].iteritems():
            os.putenv(k, v)

        for k in os.environ.iterkeys():
            if k in self.config['environment']:
                continue
            os.unsetenv(k)
        os.environ = self.config['environment']

        if self.config['network']['http']['proxy']:
            os.putenv('http_proxy', self.config['network']['http']['proxy'])
            os.environ['http_proxy'] = \
                self.config['apt']['conf']['Acquire::http::Proxy'] = \
                self.config['network']['http']['proxy']

        if self.config['network']['ftp']['proxy']:
            os.putenv('ftp_proxy', self.config['network']['ftp']['proxy'])
            os.environ['ftp_proxy'] = \
                self.config['apt']['conf']['Acquire::ftp::Proxy'] = \
                self.config['network']['ftp']['proxy']
