#!/bin/bash
sed -i "s@mute\" class=\"btn btn-outline-light hide\"@mute\" class=\"btn btn-outline-light hide\" style=\"border: 1px solid black !important; text-color: black !important; color: black !important;\"@g" web/site/$1/chat.html
