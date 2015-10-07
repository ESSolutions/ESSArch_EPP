#!/bin/bash
#
### BEGIN INIT INFO
# Provides:          httpd
# Required-Start:    $all
# Required-Stop:     $network $local_fs $remote_fs
# Default-Start:     2 3 5
# Default-Stop:      0 1 6
# Short-Description: Apache httpd server daemon
### END INIT INFO
#
# httpd        Startup script for the Apache HTTP Server
#
# chkconfig: - 85 15
# description: Apache is a World Wide Web server.  It is used to serve \
#	       HTML files and CGI.
# processname: httpd

# Source function library.
. /etc/rc.d/init.d/functions 	#SUSE11 comment out the this row


# Start httpd in the en_US.UTF-8 locale by default.
HTTPD_LANG=en_US.UTF-8

# This will prevent initlog from swallowing up a pass-phrase prompt if
# mod_ssl needs a pass-phrase from the user.
INITLOG_ARGS=""

# Set HTTPD=/usr/sbin/httpd.worker in /etc/sysconfig/httpd to use a server
# with the thread-based "worker" MPM; BE WARNED that some modules may not
# work correctly with a thread-based MPM; notably PHP will refuse to start.

# Path to the apachectl script, server binary, and short-form for messages.
apachectl=/ESSArch/pd/apache/bin/apachectl
httpd=/ESSArch/pd/apache/bin/httpd
CONFFILE=/ESSArch/config/httpd.conf
OPTIONS="-f ${CONFFILE}"
prog=httpd
pidfile=/var/run/httpd.pid
lockfile=/var/lock/subsys/httpd
RETVAL=0
export PATH=$PATH:/usr/sbin:/ESSArch/pd/python/bin
export LD_LIBRARY_PATH=/ESSArch/pd/python/lib:/ESSArch/pd/libxslt/lib:/ESSArch/pd/libxml/lib
export PYTHONPATH=/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP:/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP/workers:/ESSArch/config
export PYTHON_EGG_CACHE=/ESSArch/pd/.python-eggs

export LANG='en_US.UTF-8'
export LC_ALL='en_US.UTF-8'

# The semantics of these two functions differ from the way apachectl does
# things -- attempting to start while running is a failure, and shutdown
# when not running is also a failure.  So we just do it the way init scripts
# are expected to behave here.
start() {
        echo -n $"Starting $prog: "
        LANG=$HTTPD_LANG daemon --pidfile=$pidfile $httpd $OPTIONS
        #LANG=$HTTPD_LANG $httpd $OPTIONS		#SUSE11
        RETVAL=$?
        echo
        [ $RETVAL = 0 ] && touch ${lockfile}
        return $RETVAL
}

# When stopping httpd a delay of >10 second is required before SIGKILLing the
# httpd parent; this gives enough time for the httpd parent to SIGKILL any
# errant children.
stop() {
	echo -n $"Stopping $prog: "
	#killproc -p ${pidfile} -d 10 $httpd
	killproc -d 10 $httpd
	#killproc -t 10 $httpd		#SUSE11
	RETVAL=$?
	echo
	[ $RETVAL = 0 ] && rm -f ${lockfile} ${pidfile}
}
reload() {
    echo -n $"Reloading $prog: "
    if ! LANG=$HTTPD_LANG $httpd $OPTIONS -t >&/dev/null; then
        RETVAL=$?
        echo $"not reloading due to configuration syntax error"
        failure $"not reloading $httpd due to configuration syntax error"
    else
        #killproc -p ${pidfile} $httpd -HUP
        killproc $httpd -HUP
        RETVAL=$?
    fi
    echo
}

# See how we were called.
case "$1" in
  start)
	start
	;;
  stop)
	stop
	;;
  status)
        status -p ${pidfile} $httpd
        #status $httpd
	RETVAL=$?
	;;
  restart)
	stop
	start
	;;
  condrestart|try-restart)
        if status -p ${pidfile} $httpd >&/dev/null; then
	#if [ -f ${pidfile} ] ; then
		stop
		start
	fi
	;;
  force-reload|reload)
        reload
	;;
  graceful|help|configtest|fullstatus)
	$apachectl $@
	RETVAL=$?
	;;
  *)
	echo $"Usage: $prog {start|stop|restart|condrestart|reload|status|fullstatus|graceful|help|configtest}"
	exit 1
esac

exit $RETVAL
