#!/bin/bash

base="" # Replace with abs path to directory containing XBM icons.
for f in $(ls $base); do
    echo "Converting $f"
    abs="$base/$f"
    name="${f%.*}"
    out="$name.txt"
    touch $out
    echo $name >> $out
    xbmtopbm $abs | pnmtoplainpnm | tail -n +3 | sed 's/0/./g' | sed 's/1/X/g' >> $out
done