#!/bin/bash
#Regular runner to receive up-to-date data from SAIS.

#Obtain the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python $DIR/script/crawler.py
