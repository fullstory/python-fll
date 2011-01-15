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

    Options       Type        Description
    --------------------------------------------------------------------------
    config_file - (str)       pathname to config file
    cmdline     - (Namespace) an argparse Namespace object
    """
    def __init__(self):
        self.config_file = fll.cmdline.get_config_file()
        if self.config_file is None:
            if os.path.isfile('conf/fll.conf'):
                self.config_file = file(os.path.realpath('conf/fll.conf'))
            elif os.path.isfile('/etc/fll/fll.conf'):
                self.config_file = file('/etc/fll/fll.conf')
            else:
                raise ConfigError('no configuration file specified')

        if os.path.isfile('conf/fll.conf.spec'):
            self.config_spec = file(os.path.realpath('conf/fll.conf.spec'))
        else:
            self.config_spec = file('/usr/share/fll/fll.conf.spec')

        self.config = ConfigObj(self.config_file, configspec=self.config_spec,
                                interpolation='template')

        self._process_cmdline()
        self._config_defaults()
        self._validate_config()
        self._propogate_modes()
        self._set_environment()

        if self.config['verbosity'] == 'debug':
            import pprint
            pprint.pprint(dict(self.config))

    def _validate_config(self):
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
                              self.config_file.name)
            raise ConfigError('\n'.join(error_msgs))

    def _process_cmdline(self):
        def merge(d1, d2):
            result = dict(d1)
            for k,v in d2.iteritems():
                if k in result:
                    result[k] = merge(result[k], v)
                else:
                    result[k] = v
            return result

        args = fll.cmdline.cmdline().parse_args()

        for key, value in args.__dict__.iteritems():
            if value in [None, False]:
                continue
            if isinstance(value, file):
                continue

            keys = key.split('_')
            key = keys.pop(-1)

            config = {key: value}
            for k in reversed(keys):
                config = {k: config}

            if keys:
                self.config.update(merge(self.config, config))
            else:
                self.config.update(config)

    def _config_defaults(self):
        """Set some defaults which are not able to be set in fll.conf.spec."""
        a = fll.misc.cmd('dpkg --print-architecture', pipe=True, silent=True)
        if 'archs' not in self.config:
            self.config['archs'] = [a.strip()]

        try:
            self.config['dir'] = os.path.realpath(self.config['dir'])
        except KeyError:
            self.config['dir'] = os.getcwd()

    def _propogate_modes(self):
        """Propogate global verbosity mode to config sections."""
        mode = self.config['verbosity']

        for section in self.config.keys():
            if section == 'environment':
                continue
            if isinstance(self.config[section], dict):
                self.config[section][mode] = True

    def _set_environment(self):
        """Set environment variables as per 'environment' config
        settings. Propogate http/ftp proxy settings."""
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
