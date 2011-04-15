#!/bin/sh
set -e

WINEPREFIX=$1
DEST=$2

DEBUG=false
NSISONLY=false
PY2EXEONLY=false
QUIET=true

if [ "$3" = "-d" ]; then
   DEBUG=true
fi
if [ "$3" = "-n" ]; then
   NSISONLY=true
fi
if [ "$3" = "-p" ]; then
   PY2EXEONLY=true
fi
if [ "$3" = "-v" ]; then
   QUIET=false
fi

if [ ! -d "$WINEPREFIX" ]; then
    echo "ERROR: usage wineprefix destiation"
    exit
fi

export WINEDEBUG=fixme-all
export WINEPREFIX=$WINEPREFIX


### Create directory structure

do_cleanup() {
    if [ "$PY2EXEONLY" = "true" -o "$NSISONLY" = "true" ]; then
        return
    fi
    echo '= Cleaning target'

    rm -fr $DEST
    rm -f StoqInstaller.exe
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
    mkdir -p $DEST/etc
    mkdir -p $DEST/share
    mkdir -p $DEST/share/locale
    mkdir -p $DEST/share/themes
    mkdir -p $DEST/lib/gtk-2.0/2.10.0/engines
}


### Run setup.py on kiwi

do_install_deps() {
    if [ "$PY2EXEONLY" = "true" -o "$NSISONLY" = "true" ]; then
        return
    fi

    echo '= Installing dependencies'

    cd ../kiwi; wine c:/Python26/pythonw.exe setup.py -q install 2> /dev/null
    cd ../stoqdrivers; wine c:/Python26/pythonw.exe setup.py -q install 2> /dev/null
    cd ../stoqlib; wine c:/Python26/pythonw.exe setup.py -q install 2> /dev/null

    cd ../stoq
}


### Copy over dlls py2exe can't find

do_copy_data() {
    if [ "$PY2EXEONLY" = "true" -o "$NSISONLY" = "true" ]; then
        return
    fi

    echo '= Copying dlls & application data'

    # Python
    cp $WINEPREFIX/drive_c/Python26/python26.dll $DEST
    cp $WINEPREFIX/drive_c/Python26/DLLs/tcl85.dll $DEST
    cp $WINEPREFIX/drive_c/Python26/DLLs/tk85.dll $DEST

    # Postgres client libraries, 8.4.7 specific
    PGSQLDIR=$WINEPREFIX/drive_c/pgsql
    cp $PGSQLDIR/bin/comerr32.dll $DEST
    cp $PGSQLDIR/bin/gssapi32.dll $DEST
    cp $PGSQLDIR/bin/krb5_32.dll $DEST
    cp $PGSQLDIR/bin/k5sprt32.dll $DEST
    cp $PGSQLDIR/bin/libeay32.dll $DEST
    cp $PGSQLDIR/bin/libeay32.dll $DEST
    cp $PGSQLDIR/bin/libiconv-2.dll $DEST
    cp $PGSQLDIR/bin/libintl-8.dll $DEST
    cp $PGSQLDIR/bin/libpq.dll $DEST
    cp $PGSQLDIR/bin/msvcr71.dll $DEST
    cp $PGSQLDIR/bin/psql.exe $DEST
    cp $PGSQLDIR/bin/ssleay32.dll $DEST

    # Gtk+
    GTKDIR=$WINEPREFIX/drive_c/Python26/Lib/site-packages/gtk-2.0/runtime
    GTKBIN=$GTKDIR/bin
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

    # Gtk+ Theme
    cp -r $GTKDIR/etc/gtk-2.0/ $DEST/etc
    cp -r $GTKDIR/lib/gtk-2.0/2.10.0/engines/libwimp.dll $DEST/lib/gtk-2.0/2.10.0/engines
    cp -r $GTKDIR/share/themes/MS-Windows $DEST/share/themes
    cp -r $GTKDIR/share/locale/pt_BR/ $DEST/share/locale

    # Gazpacho
    cp $WINEPREFIX/drive_c/Python26/share/gazpacho/pixmaps/* $DEST/pixmaps

    # Kiwi/Stoqlib/Stoqdrivers/Stoq
    # Huge mess, should all go into share/
    cp $DEST/../../kiwi/pixmaps/* $DEST/pixmaps
    cp $DEST/../../stoqlib/data/pixmaps/* $DEST/data/pixmaps
    cp $DEST/../../stoqlib/data/glade/* $DEST/data/glade
    cp $DEST/../../stoqlib/data/sql/* $DEST/data/sql
    cp $DEST/../../stoqlib/data/csv/* $DEST/data/csv
    cp $DEST/../../stoqlib/data/fonts/* $DEST/data/fonts
    cp -r $DEST/../../stoqlib/plugins/* $DEST/plugins
    cp $DEST/../../stoq/data/glade/* $DEST/data/glade
    cp $DEST/../../stoq/data/pixmaps/* $DEST/data/pixmaps
    cp $DEST/../../kiwi/glade/* $DEST/data/glade
    cp -r $WINEPREFIX/drive_c/Python26/share/locale/* $DEST/share/locale
}


### Compact python itself + all python code into a big exe

do_py2exe() {
    if [ "$NSISONLY" = "true" ]; then
        return
    fi

    echo '= Creating executable via py2exe'

    PYTHONPATH=`pwd`/../stoqlib\;`pwd`/../kiwi\;`pwd`/../stoqdrivers \
        PATH=$GTKBIN\;$PATH \
        WINEPREFIX=$WINEPREFIX \
        wine c:/Python26/pythonw.exe -W ignore::DeprecationWarning setup.py -q py2exe

    # This is unneeded, py2exe copies over all of it for some reason
    rm -fr $DEST/tcl
    # Not necessary for now - just documentation
    rm -fr $DEST/plugins/nfe/docs
}


### Create the installer

do_makensis() {
    if [ "$PY2EXEONLY" = "true" ]; then
        return
    fi

    REVISION=`bzr log -r revno:-1|egrep ^revno:|cut -d\  -f2`
    VERSION=`cat stoq/__init__.py|egrep ^version|cut -d\" -f2`
    DATE=`date +%Y%M%d_%H%M%S`
    NSISOPTS="-DDATE=$DATE -DVERSION=$VERSION -DREVISION=$REVISION"

    if [ "$QUIET" = "true" ]; then
        NSISOPTS="$NSISOPTS -V1"
    fi

    if [ "$DEBUG" = "true" ]; then
        NSISOPTS="$NSISOPTS -DDEBUG=1"
        KIND="debug"
    else
        KIND="release"
    fi

    echo "= Creating $KIND installer"
    makensis $NSISOPTS stoq.nsis
}

do_cleanup
do_install_deps
do_copy_data
do_py2exe
do_makensis

OUTPUT=StoqInstaller-r$REVISION.exe
mv StoqInstaller.exe $OUTPUT
echo "$OUTPUT created"
