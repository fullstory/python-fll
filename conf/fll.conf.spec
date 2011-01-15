dir		= string(min=1, default=None)
uid		= integer(default=0)
gid		= integer(default=0)

archs		= list()
mirror		= string(min=1, default='http://cdn.debian.net/debian/')

dryrun		= boolean(default=False)
verbosity	= option('quiet', 'verbose', 'debug', default='quiet')
__many__	= string(min=1)

[network]
quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

[[ftp]]
proxy		= string(min=1, default=None)
[[http]]
proxy		= string(min=1, default=None)

[apt]
src		= boolean(default=False)

quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

[[key]]
disable		= boolean(default=False)
server		= string(min=1, default='wwwkeys.eu.pgp.net')

[[conf]]
APT::Install-Recommends = string(min=1, default='false')
__many__	= string(min=1)

[[sources]]
[[[debian]]]
description	= string(min=1, default='Debian GNU/Linux')
uri		= string(min=1, default='$mirror')
final_uri	= string(min=1, default=None)
suites		= list(default=list('sid'))
components	= list(default=list('main'))

[[[__many__]]]
description	= string(min=1)
uri		= string(min=1)
final_uri	= string(min=1, default=None)
suites		= list(default=list('sid'))
components	= list(default=list('main'))

[chroot]
preserve	= boolean(default=False)

quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

[[bootstrap]]
utility		= option('cdebootstrap', 'debootstrap', default='cdebootstrap')
suite		= string(min=1, default='sid')
uri		= string(min=1, default='$mirror')
flavour		= option('minimal', 'build', 'standard', default='minimal')
include		= string(min=1, default=None)
exclude		= string(min=1, default=None)
quiet		= boolean(default=False)
verbose		= boolean(default=False)
debug		= boolean(default=False)

[environment]
PATH		= string(min=1, default='/usr/sbin:/usr/bin:/sbin:/bin')
HOME		= string(min=1, default='/root')
SHELL		= string(min=1, default='/bin/bash')
LANGUAGE	= string(min=1, default='C')
LC_ALL		= string(min=1, default='C')
LANG		= string(min=1, default='C')
DEBIAN_FRONTEND	= string(min=1, default='noninteractive')
DEBIAN_PRIORITY	= string(min=1, default='critical')
__many__	= string(min=1)
