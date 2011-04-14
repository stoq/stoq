#!/bin/sh
WINEPREFIX=$1
DEST=$2

GTKDIR=$WINEPREFIX/drive_c/Python26/Lib/site-packages/gtk-2.0/runtime
GTKBIN=$GTKDIR/bin

### Create directory structure

echo '= Cleaning target'

rm -fr $DEST
mkdir -p $DEST
mkdir -p $DEST/glade
mkdir -p $DEST/pixmaps
mkdir -p $DEST/data/pixmaps
mkdir -p $DEST/data/glade
mkdir -p $DEST/data/config
mkdir -p $DEST/data/fonts
mkdir -p $DEST/data/template
mkdir -p $DEST/data/sql
mkdir -p $DEST/data/csv
mkdir -p $DEST/plugins
mkdir -p $DEST/stoqdrivers/conf
mkdir -p $DEST/catalogs
mkdir -p $DEST/resources
mkdir -p $DEST/pixmaps/kiwi
mkdir -p $DEST/share
mkdir -p $DEST/share/locale

### Run setup.py on kiwi

echo '= Installing dependencies'

cd ../kiwi; WINEPREFIX=$1 wine c:/Python26/pythonw.exe setup.py -q install
cd ../stoqdrivers; WINEPREFIX=$1 wine c:/Python26/pythonw.exe setup.py -q install
cd ../stoqlib; WINEPREFIX=$1 wine c:/Python26/pythonw.exe setup.py -q install

cd ../stoq

### Copy over dlls py2exe can't find

echo '= Copying dlls & application data'

# Python
cp $WINEPREFIX/drive_c/Python26/python26.dll $DEST
cp $WINEPREFIX/drive_c/Python26/DLLs/tcl85.dll $DEST
cp $WINEPREFIX/drive_c/Python26/DLLs/tk85.dll $DEST

# Gtk+
cp $GTKBIN/libglib-2.0-0.dll $DEST
cp $GTKBIN/libgthread-2.0-0.dll $DEST
cp $GTKBIN/libgmodule-2.0-0.dll $DEST
cp $GTKBIN/libgobject-2.0-0.dll $DEST
cp $GTKBIN/libgio-2.0-0.dll $DEST
cp $GTKBIN/libatk-1.0-0.dll $DEST
cp $GTKBIN/libcairo-2.dll $DEST
cp $GTKBIN/libcairo-gobject-2.dll $DEST
cp $GTKBIN/libfontconfig-1.dll $DEST
cp $GTKBIN/libexpat-1.dll $DEST
cp $GTKBIN/freetype6.dll $DEST
cp $GTKBIN/libpng14-14.dll $DEST
cp $GTKBIN/zlib1.dll $DEST
cp $GTKBIN/libpango-1.0-0.dll $DEST
cp $GTKBIN/libpangocairo-1.0-0.dll $DEST
cp $GTKBIN/libpangoft2-1.0-0.dll $DEST
cp $GTKBIN/libpangowin32-1.0-0.dll $DEST
cp $GTKBIN/libgdk_pixbuf-2.0-0.dll $DEST
cp $GTKBIN/libgdk-win32-2.0-0.dll $DEST
cp $GTKBIN/libgtk-win32-2.0-0.dll $DEST
cp $GTKBIN/intl.dll $DEST
cp -r $GTKDIR/share/locale/pt_BR/ $DEST/share/locale

# Gazpacho
cp $WINEPREFIX/drive_c/Python26/share/gazpacho/pixmaps/* $DEST/pixmaps

# Kiwi/Stoqlib/Stoqdrivers/Stoq
# Huge mess, should all go into share/
cp $DEST/../../kiwi/pixmaps/* $DEST/pixmaps
cp $DEST/../../stoqlib/data/pixmaps/* $DEST/data/pixmaps
cp $DEST/../../stoqlib/data/glade/* $DEST/data/glade
cp $DEST/../../stoqlib/data/sql/* $DEST/data/sql
cp $DEST/../../stoqlib/data/fonts/* $DEST/data/fonts
cp $DEST/../../stoq/data/glade/* $DEST/data/glade
cp $DEST/../../stoq/data/pixmaps/* $DEST/data/pixmaps
cp $DEST/../../kiwi/glade/* $DEST/data/glade
cp -r $WINEPREFIX/drive_c/Python26/share/locale/* $DEST/share/locale

### Compact python itself + all python code into a big exe
echo '= Creating executable via py2exe'

PYTHONPATH=`pwd`/../stoqlib\;`pwd`/../kiwi\;`pwd`/../stoqdrivers \
  PATH=$GTKBIN\;$PATH \
  WINEPREFIX=$1 \
  wine c:/Python26/pythonw.exe setup.py -q py2exe

# This is unneeded, py2exe copies over all of it for some reason
rm -fr $DEST/tcl

### Create the installer
echo '= Creating installer'
makensis -V2 stoq.nsis
