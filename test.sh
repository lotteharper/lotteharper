#!/bin/bash
LANG="de"
CMD_INIT="s/remoteSocket.send(data.ip);/remoteSocket.send(JSON.stringify(data));/g"
CMD=$CMD_INIT
echo $CMD
for file in /home/team/lotteh/web/site/*/*; do
    echo "Processing $file"
    sed -i -e $CMD "$file"
done
