"""
This is the fll.config module, it provides a class for abstracting the
fll configuration file.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""

from configobj import ConfigObj, ConfigObjError, flatten_errors
from validate import Validator
import os


class ConfigError(Exception):
    """
    An Error class for use by Config.
    """
    pass


class Config(object):
    """
    A class for preparing and using apt within a chroot.

    Arguments:
    config_file - pathname to config file
    """

    def __init__(self, config_file):
        self.config_file = os.path.realpath(config_file)
