#!/bin/bash

for f in $(find . -name "*_actual.png"); do
    golden_name=$(sed 's/_actual/_golden/g' <<< $f)
    rm $golden_name
    mv $f $golden_name
done