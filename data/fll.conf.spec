[ 'apt' ]
[[ 'conf' ]]
APT::Install-Recommends = string(min=1, default='false')
__many__ = string(min=1)

[[ 'sources' ]]
[[[ 'debian' ]]]
description = string(min=1, default='Debian GNU/Linux')
uri         = string(min=1, default='http://cdn.debian.net/debian/')
suites      = string(min=1, default='sid')
components  = string(min=1, default='main')

[[[ __many__ ]]]
description = string(min=1)
uri         = string(min=1)
suites      = string(min=1)
components  = string(min=1)
