#!/bin/bash

APPHOME=`dirname "$0"`
APPHOME=`cd "$APPHOME"; pwd`

echo "run at "$APPHOME
/usr/local/domob/current/logtailer3/bin/logtailer.sh -d $APPHOME $@


