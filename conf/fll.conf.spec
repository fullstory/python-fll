__many__		= string(min=1)

[ 'apt' ]
fetch_src		= boolean(default=False)
keyserver		= string(min=1, default='wwwkeys.eu.pgp.net')
	
[[ 'conf' ]]
APT::Install-Recommends = string(min=1, default='false')
__many__		= string(min=1)

[[ 'sources' ]]
[[[ 'debian' ]]]
description		= string(min=1, default='Debian GNU/Linux')
uri			= string(min=1, default='http://cdn.debian.net/debian/')
suites			= string(min=1, default='sid')
components		= string(min=1, default='main')

[[[ __many__ ]]]
description		= string(min=1)
uri			= string(min=1)
suites			= string(min=1)
components		= string(min=1)

[ 'chroot' ]
preserve		= boolean(default=False)
hostname		= string(min=1, default='chroot')

[[ 'bootstrap' ]]
bootstrapper		= option('cdebootstrap', 'debootstrap', default='cdebootstrap')
suite			= string(min=1, default='sid')
uri			= string(min=1, default='http://cdn.debian.net/debian/')
flavour			= option('minimal', 'build', 'standard', default='minimal')
include			= string(min=1, default=None)
exclude			= string(min=1, default=None)
quiet			= boolean(default=False)
verbose			= boolean(default=False)
debug			= boolean(default=False)

[ 'environment' ]
PATH			= string(min=1, default='/usr/sbin:/usr/bin:/sbin:/bin')
HOME			= string(min=1, default='/root')
SHELL			= string(min=1, default='/bin/bash')
LANGUAGE		= string(min=1, default='C')
LC_ALL			= string(min=1, default='C')
LANG			= string(min=1, default='C')
DEBIAN_FRONTEND		= string(min=1, default='noninteractive')
DEBIAN_PRIORITY		= string(min=1, default='critical')
__many__		= string(min=1)
