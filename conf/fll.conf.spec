[ 'architectures' ]
__many__ = string(min=3,max=1000)

[ 'packages' ]
__many__ = string(min=3,max=1000)

[ 'distro' ]
__many__ = string(min=3,max=1000)

[ 'options' ]
__many__ = string(min=3,max=1000)

[ 'apt' ]
[[ 'preferences' ]]
__many__ = string(min=3,max=1000)

[[ 'sources' ]]
[[[ __many__ ]]]
description = string(min=3,max=1000)
uri         = string(min=3,max=1000)
suite       = string(min=3,max=1000)
components  = string(min=3,max=1000)
