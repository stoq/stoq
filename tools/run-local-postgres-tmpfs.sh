PGVERSION=9.1
PGDIR=`pwd`/_postgresql
CONF=$PGDIR/db/postgresql.conf
rm -fr $PGDIR
mkdir $PGDIR
sudo mount none -t tmpfs $PGDIR
mkdir $PGDIR/run
/usr/lib/postgresql/$PGVERSION/bin/initdb $PGDIR/db

# Specify unix socket directory
sed -i $CONF \
    -e "s,#unix_socket_directory = '',unix_socket_directory = '$PGDIR/run',g" \
    -e "s,#listen_addresses = 'localhost',listen_addresses = '',g" \
    -e "s,#fsync = on,fsync = off,g" \
    -e "s,#synchronous_commit = on,synchronous_commit = off,g" \
    -e "s,#full_page_writes = on,full_page_writes = off,g" \
    -e "s,#bgwriter_lru_maxpages = 100,bgwriter_lru_maxpages = 0,g"

/usr/lib/postgresql/$PGVERSION/bin/postgres -F -D $PGDIR/db
