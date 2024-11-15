#!/bin/bash
echo "test"
GIT_REPO='https://gitlab.com/jasperholton/lotteh2024-11-09'
GIT_PROJ=`echo $GIT_REPO | rev | cut -d/ -f1 | rev`
echo $GIT_PROJ
FILE="result is ${GIT_PROJ}"
echo $FILE
