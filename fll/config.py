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

    Options       Type        Description
    --------------------------------------------------------------------------
    config_file - (str)       pathname to config file
    cmdline     - (Namespace) an argparse Namespace object
    """
    def __init__(self):
        self.config_file = fll.cmdline.get_config_file()
        if self.config_file is None:
            if os.path.isfile('conf/fll.conf'):
                self.config_file = os.path.realpath('conf/fll.conf')
            elif os.path.isfile('/etc/fll/fll.conf'):
                self.config_file = '/etc/fll/fll.conf'
            else:
                raise ConfigError('no configuration file specified')

        if os.path.isfile('conf/fll.conf.spec'):
            self.config_spec = os.path.realpath('conf/fll.conf.spec')
        else:
            self.config_spec = '/usr/share/fll/fll.conf.spec'

        self.config = ConfigObj(self.config_file, configspec=self.config_spec,
                                interpolation='template')

        # These sections of the configuration accept command line and mode
        # options and are used by _process_cmdline() and _propogate_modes()
        self._option_sections = ['apt', 'chroot']

        self._process_cmdline()
        self._propogate_modes()
        self._validate()
        self._set_environment()

        if self.config['verbosity'] == 'debug':
            import pprint
            pprint.pprint(dict(self.config))

    def _validate(self):
        result = self.config.validate(Validator(), preserve_errors=True)
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
                              self.config_file)
            raise ConfigError('\n'.join(error_msgs))

    def _process_cmdline(self):
        args = fll.cmdline.cmdline().parse_args()

        for key, value in args.__dict__.iteritems():
            if value in [None, False]:
                continue
            if isinstance(value, file):
                continue

            keys = key.split('_', 1)
            if len(keys) >= 1 and keys[0] in self._option_sections:
                section, key = keys
                if section in self.config:
                    self.config[section][key] = value
                else:
                    self.config[section] = {key: value}
            else:
                self.config[key] = value

    def _propogate_modes(self):
        mode = self.config['verbosity']

        for section in self._option_sections:
            if section in self.config:
                self.config[section][mode] = True
            else:
                self.config[section] = {mode: True}

    def _set_environment(self):
        for k, v in self.config['environment'].iteritems():
            os.putenv(k, v)

        for k in os.environ.iterkeys():
            if k in self.config['environment']:
                continue
            os.unsetenv(k)
        os.environ = self.config['environment']

        if self.config['http_proxy']:
            os.putenv('http_proxy', self.config['http_proxy'])
            os.environ['http_proxy'] = \
                self.config['apt']['conf']['Acquire::http::Proxy'] = \
                self.config['http_proxy']

        if self.config['ftp_proxy']:
            os.putenv('ftp_proxy', self.config['ftp_proxy'])
            os.environ['ftp_proxy'] = \
                self.config['apt']['conf']['Acquire::ftp::Proxy'] = \
                self.config['ftp_proxy']
