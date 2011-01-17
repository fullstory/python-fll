"""
This is the fll.distro module, it abstracts the 'distro' section of an
fll.config.Config object. It provides methods for writing the
/etc/distro-release and /etc/default/distro files.

Authour:   Kel Modderman
Copyright: Copyright (C) 2010 Kel Modderman <kel@otaku42.de>
License:   GPL-2
"""


class DistroError(Exception):
    pass


class Distro(object):
    pass
