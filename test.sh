#!/bin/bash
LANG="de"
CMD_INIT="s/class=\"nav-link\" href=\"/links\"/class=\"nav-link\" href=\"${LANG}\/links\"/g"
#s@class="nav-link" href="/links"@class="nav-link" href="$LANG/links"@g'`
CMD=$CMD_INIT
echo $CMD
sed -e $CMD /home/team/lotteh/test.txt

