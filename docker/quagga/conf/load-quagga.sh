#!/bin/sh

sleep 0.1
vtysh << __END__
conf term
`cat $1`
__END__

exit 0
