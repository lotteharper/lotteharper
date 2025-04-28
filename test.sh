#!/bin/bash
USER_NAME='team'
PROJECT_NAME='lotteh'
GIT_URL_PROJ='ch.git'
REPO_DATE='meme'
PROJECT_GIT_URL="${GIT_URL_PROJ%.*}.$REPO_DATE"
echo "$PROJECT_GIT_URL"
