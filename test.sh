#!/bin/bash
DIR="/home/team/lotteh"
USER="team"
GIT_REPO="https://github.com/daisycamber/lotteharper.git"
GIT_URL=`sed -n '4p' < $DIR/config/git`
echo $GIT_URL
escaped_url=$(echo "$GIT_URL" | sed 's/\//\\\//g')
CMD="4s/GIT_REPO.*/GIT_REPO=\"$escaped_url\"/g"
echo $CMD
sed -i -e $CMD $DIR/test.sh
