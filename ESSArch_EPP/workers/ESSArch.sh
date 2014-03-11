#! /bin/sh
#
# System startup script for ESSArch
#

PythonBin=/ESSArch/pd/python/bin/python2.7
ESSArchStopStart=/ESSArch/bin/ESSArchStopStart.pyc
test -x $PythonBin || exit 5

case "$1" in
    start)
        echo "Starting ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -s"
        ;;
    stop)
        echo "Shutting down ESSArch"
        su - arch -c "$PythonBin $ESSArchStopStart -q" 
        ;;
    status)
        echo "Checking ESSArch procs"
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac
