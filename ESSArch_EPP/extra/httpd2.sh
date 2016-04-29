#!/bin/sh
### BEGIN INIT INFO
# Provides:          apache2
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: apache2
# Description:       httpd server for serving web content
### END INIT INFO
# processname: httpd

apachectl=/ESSArch/pd/apache/bin/apachectl
CONFFILE=/ESSArch/config/httpd.conf
OPTIONS="-f ${CONFFILE}"
export LANG=en_US.UTF-8
export PATH=/ESSArch/pd/python/bin:$PATH:/usr/sbin
export LD_LIBRARY_PATH=/ESSArch/pd/python/lib:/ESSArch/pd/libxslt/lib:/ESSArch/pd/libxml/lib
export PYTHONPATH=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP:/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP/workers:/ESSArch/config
export PYTHON_EGG_CACHE=/ESSArch/pd/.python-eggs

case "$1" in
start)
        echo "Starting Apache ..."
        $apachectl $OPTIONS -k start
;;
stop)
        echo "Stopping Apache ..."
        $apachectl $OPTIONS -k stop
;;
graceful)
        echo "Restarting Apache gracefully..."
        $apachectl $OPTIONS -k graceful
;;
restart)
        echo "Restarting Apache ..."
        $apachectl $OPTIONS -k restart
;;
*)
        echo "Usage: '$0' {start|stop|restart|graceful}"
        exit 64
;;
esac
exit 0
