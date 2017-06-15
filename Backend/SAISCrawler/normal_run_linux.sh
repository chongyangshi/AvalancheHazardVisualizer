#!/bin/bash
#Regular runner to receive up-to-date data from SAIS.

#Obtain the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#Launch Xvfb session for linux
Xvfb -auth /etc/X99.cfg :99 -screen scrn 1280x1024x16 &
export DISPLAY=:99

python $DIR/script/crawler.py

killall Xvfb
