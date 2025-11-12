#!/bin/bash
return_code=0
/home/team/lotteh/venv/bin/python /home/team/lotteh/pam.py
return_code=$(($return_code + $?))
echo $return_code
if [ $return_code == 0 ]; then
    echo "Your login has succeeded. Please continue." >> /dev/stdout
    exit 0
else
    echo "Your login has been denied due to lack of authentication. Key-based auth was successful but no secondary authentication was provided. No further information is available about this error." >> /dev/stderr
    exit 103
fi
