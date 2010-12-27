[ 'apt' ]
[[ 'conf' ]]
__many__ = string(min=3,max=1000)

[[ 'sources' ]]
[[[ __many__ ]]]
description = string(min=3,max=1000)
uri         = string(min=3,max=1000)
suite       = string(min=3,max=1000)
components  = string(min=3,max=1000)
