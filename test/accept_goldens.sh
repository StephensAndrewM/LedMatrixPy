#!/bin/bash

base=$(pwd)

if [[ $base != *"/test" ]]; then
    base="$base/test"
fi

for f in $(find $base -name "*_actual.png"); do
    golden_name=$(sed 's/_actual/_golden/g' <<< $f)
    rm $golden_name 2>/dev/null
    mv $f $golden_name
done