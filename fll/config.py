"""
This is the fll.config module, it provides a class for abstracting the
fll configuration file and command line arguments.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from configobj import ConfigObj, ConfigObjError, \
                      flatten_errors, get_extra_values
from validate import Validator
import fll.cmdline
import fll.misc
import os
import sys


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
        self.config_file = fll.cmdline.get_config_file()
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

            cmdline.Namespace('apt_sources_debian_uri') = value
            |
            `-> config['apt']['sources']['debian']['uri'] = value
        """
        cmdline = fll.cmdline.cmdline().parse_args()

        for key, value in cmdline.__dict__.iteritems():
            if value in [None, False]:
                continue
            if isinstance(value, file):
                continue

            keys = key.split('_')
            key = keys.pop(-1)

            config = {key: value}
            for k in reversed(keys):
                config = {k: config}

            self.config.merge(config)

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
            if section in ['environment', 'network']:
                continue
            if isinstance(self.config[section], dict):
                for m in other_modes:
                    if self.config[section][m] is True:
                        break
                else:
                    self.config[section][mode] = True

    def _debug_configobj(self):
        """Dump configuration object to file."""
        dump_file = fll.cmdline.get_dump_file()
        if dump_file is None:
            self.config.write(sys.stdout)
        else:
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
