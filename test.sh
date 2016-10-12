#!/usr/bin/env bash

if [[ ! -f "$1" ]]; then
   echo "The file doesn't exists: '$1'"
   exit 2
fi

if [[ ! -d "$2" ]]; then
   echo "The output folder doesn't exists: '$2'"
   exit 3
fi

tmpFile=`mktemp`
destFile="$(basename $1).chcfg"
./cube2chibi.py --ioc $1 --cube $STM32_CUBEMX --output $tmpFile

sizeOf=`stat --printf="%s" $tmpFile`

echo "File size is $sizeOf"

if [[ "$sizeOf" == "0" ]]; then
   echo "File is empty $destFile"
fi

mv $tmpFile "$2/$destFile"


