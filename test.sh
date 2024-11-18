#!/bin/bash
echo "test"
GIT_REPO='https://github.com/daisycamber/lotteharper.git'
# Add your project name and username here
PROJECT_NAME="yourproject"
USER_NAME="team"
GIT_PROJ=`echo $GIT_REPO | rev | cut -d/ -f1 | rev  | cut -d. -f1`
echo $GIT_PROJ

