#!/bin/bash

version=$1

regex="([0-9]+)\.([0-9]+)\.?([0-9]*)?(~([a-z]*[0-9]*))?"
if [[ $version =~ $regex ]]
then
    major=${BASH_REMATCH[1]}
    minor=${BASH_REMATCH[2]}
    micro=${BASH_REMATCH[3]:-0}
    extra=${BASH_REMATCH[5]}
else
    echo "Version doesn't match expected regex"
    exit 1
fi

dch -v $1 "Release $version"
sed -i s/UNRELEASED/xenial/ debian/changelog
year=`date +%Y`
month=`date +%m | sed "s/^0//"`
day=`date +%d`

sed -i "s/major_version = .*/major_version = $major/" stoq/__init__.py
sed -i "s/minor_version = .*/minor_version = $minor/" stoq/__init__.py
sed -i "s/micro_version = .*/micro_version = $micro/" stoq/__init__.py
sed -i "s/extra_version = .*/extra_version = '$extra'/" stoq/__init__.py
sed -i "s/release_date = .*/release_date = ($year, $month, $day)/" stoq/__init__.py
