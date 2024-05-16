#!/bin/zsh
ls *LibDoc*/*/Export/**/*.xml|sed -e 's,.*Export/,,'|sort -u > allmodules
for i in $(cat allmodules); do
    mkdir -p LibDoc/$(dirname $i)
    ./psp_libdoc_2.py -l *LibDoc*/*/Export/$i -c LibDoc/$i
done

