#! /bin/sh
#
# System startup script for ESSArch
#
# chkconfig: - 84 15
#
### BEGIN INIT INFO
# Provides:          essarch
# Required-Start:    $all
# Required-Stop:     $network $local_fs $remote_fs $portmap
# Default-Start:     2 3 5
# Default-Stop:      0 1 6
# Short-Description: ESSArch worker daemons
### END INIT INFO

PythonBin=/ESSArch/pd/python/bin/python2.7
ESSArchStopStart=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP/workers/ESSArchStopStart.pyc
test -x $PythonBin || exit 5
LOCK_FILE=/var/lock/subsys/essarch

case "$1" in
    start)
        echo "Starting ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -s"
        if [ -n "$LOCK_FILE" ] ; then
            touch $LOCK_FILE
        fi        
    ;;
    stop)
        echo "Shutting down ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -q" 
        if [ -n "$LOCK_FILE" ] ; then
            rm -f $LOCK_FILE
        fi
    ;;
    status)
        echo "Checking ESSArch procs"
    ;;
    restart)
        echo "Shutting down ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -q" 
        if [ -n "$LOCK_FILE" ] ; then
            rm -f $LOCK_FILE
        fi
        echo "Starting ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -s"
        if [ -n "$LOCK_FILE" ] ; then
            touch $LOCK_FILE
        fi                
    ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
