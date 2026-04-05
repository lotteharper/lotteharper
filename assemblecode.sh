#!/bin/bash
cd /home/team/lotteharper-main
for file in */*.py; do
    echo "--- New file ---"
    ls $file
    cat $file
done
