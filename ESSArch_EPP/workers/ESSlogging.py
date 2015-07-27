#!/usr/bin/env /ESSArch/pd/python/bin/python
# coding: iso-8859-1
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB, Henrik Ek

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
import cPickle
import logging
import logging.handlers
import SocketServer
import socket, time, traceback
import struct
import sys
import ESSDB
from multiprocessing import Process
from optparse import OptionParser

#class SingleLevelFilter(logging.Filter): 
#    def __init__(self, passlevel, reject): 
#        self.passlevel = passlevel 
#        self.reject = reject 
# 
#    def filter(self, record): 
#        if self.reject: 
#            return (record.levelno != self.passlevel) 
#        else: 
#            return (record.levelno == self.passlevel) 

class ESSSocketHandler(logging.handlers.SocketHandler):
    def createSocket(self):
        """
        Try to create a socket
        """
        now = time.time()
        # Either retryTime is None, in which case this
        # is the first time back after a disconnect, or
        # we've waited long enough.
        if self.retryTime is None:
            attempt = 1
        else:
            attempt = (now >= self.retryTime)
        if attempt:
            try:
                self.sock = self.makeSocket()
                self.retryTime = None # next time, no delay before trying
            except socket.error,(why):
                raise socket.error("Problem to make TCP socket to logging server, error: %s, #record: %s" % (str(why),str(self.record)))
                #Creation failed, so set the retry time and return.
                if self.retryTime is None:
                    self.retryPeriod = self.retryStart
                else:
                    self.retryPeriod = self.retryPeriod * self.retryFactor
                    if self.retryPeriod > self.retryMax:
                        self.retryPeriod = self.retryMax
                self.retryTime = now + self.retryPeriod

    def send(self, s):
        """
        Send a pickled string to the socket.
        """
        if self.sock is None:
            self.createSocket()
        if self.sock:
            try:
                if hasattr(self.sock, "sendall"):
                    self.sock.sendall(s)
                else:
                    sentsofar = 0
                    left = len(s)
                    while left > 0:
                        sent = self.sock.send(s[sentsofar:])
                        sentsofar = sentsofar + sent
                        left = left - sent
            except socket.error,(why):
                raise socket.error("Problem to send logrecord to logging server, error: %s, #record: %s" % (str(why),str(self.record)))
                self.sock.close()
                self.sock = None  # so we can call createSocket next time
        else:
            raise socket.error("Missing TCP socket, error: %s, #record: %s" % (str('unknown'),str(self.record)))

    def handleError(self, record):
        """
        Handle an error during logging.
        """
        if self.closeOnError and self.sock:
            self.sock.close()
            self.sock = None        #try to reconnect next time
        else:
            ei = sys.exc_info()
            try:
                traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
                sys.exit(1)
            except IOError:
                pass    # see issue 5971
            finally:
                del ei

    def emit(self, record):
        """
        Emit a record.

        Pickles the record and writes it to the socket in binary format.
        If there is an error with the socket, silently drop the packet.
        If there was a problem with the socket, re-establishes the
        socket.
        """
        self.record = record
        try:
            s = self.makePickle(record)
            self.send(s)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def close(self):
        """
        Closes the socket.
        """
        if self.sock:
            self.sock.close()
            self.sock = None
        logging.Handler.close(self)

class nameFilter(logging.Filter): 
    def __init__(self, name): 
        self.name = name 
 
    def filter(self, record): 
        if record.name == self.name: 
            return True 
        else: 
            return False 

class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while 1:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return cPickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        #print 'record: %s' % str(record)
        #print 'record.levelno: %s' % str(record.levelno)
        #print 'record.name: %s' % str(record.name)
        logger.handle(record)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    """simple TCP socket-based logging receiver.
    """

    allow_reuse_address = 1

    def __init__(self, host='localhost',
                 port=60100,
                 handler=LogRecordStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        logging.info('ESS logging server running')
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

def main():
    #LogLevel = logging.INFO
    LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 1
    Console = 1

    ##########################
    # Log format
    if MultiProc:
        essFormatter1 = logging.Formatter('%(asctime)s %(name)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(name)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
    else:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
    ###########################
    # LocalFileHandler
    LogFile = '/tmp/IOEngine.log'
    #essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_IOEngine = logging.handlers.TimedRotatingFileHandler(LogFile, when='M', interval=1, backupCount=1040)
    LocalFileHandler_IOEngine.setLevel(LogLevel)
    LocalFileHandler_IOEngine.setFormatter(essFormatter1)
    LocalFileHandler_IOEngine.addFilter(nameFilter('IOEngine'))
    ###########################
    # LocalFileHandler
    LogFile = '/tmp/AIPWriter.log'
    #essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_AIPWriter = logging.handlers.TimedRotatingFileHandler(LogFile, when='M', interval=1, backupCount=1040)
    LocalFileHandler_AIPWriter.setLevel(LogLevel)
    LocalFileHandler_AIPWriter.setFormatter(essFormatter1)
    LocalFileHandler_AIPWriter.addFilter(nameFilter('AIPWriter'))
    #essLocalFileHandler.doRollover()
    ###########################
    # LocalConsoleHandler
    essConsoleHandler = logging.StreamHandler(sys.stdout)
    essConsoleHandler.setLevel(LogLevel)
    essConsoleHandler.setFormatter(essFormatter2)
    ##########################
    # Add handlers to default logger
    rootlogger = logging.getLogger('')
    rootlogger.setLevel(0)
    #rootlogger.addHandler(LocalFileHandler_IOEngine)
    #logger_IOEngine = logging.getLogger('IOEngine')
    #logger_IOEngine.addHandler(LocalFileHandler_IOEngine)
    rootlogger.addHandler(LocalFileHandler_IOEngine)
    #logger_AIPWriter = logging.getLogger('AIPWriter')
    #logger_AIPWriter.addHandler(LocalFileHandler_AIPWriter)
    rootlogger.addHandler(LocalFileHandler_AIPWriter)
    if Console:
        rootlogger.addHandler(essConsoleHandler)

    global abort_main
    abort_main = 0
    tcpserver = LogRecordSocketReceiver()
    print "About to start TCP server..."
    p1 = Process(target=tcpserver.serve_until_stopped)
    p1.start()
    #tcpserver.serve_until_stopped()
    time.sleep(10)
    print 'try to stop'
    abort_main = 1
    #p1.terminate()

if __name__ == "__main__":
    ProcName = 'ESSlogging'
    ProcVersion = __version__

    op = OptionParser(prog=ProcName,usage="usage: %prog [options] arg", version="%prog Version " + str(ProcVersion))
    op.add_option("-x", "--LogLevel", help="Set LogLevel (LEVEL: CRITICAL, ERROR, WARNING, INFO, DEBUG) (Default INFO)", dest="LogLevel", metavar="LEVEL")
    op.add_option("-p", "--process", help="ESSArch process", action="store_true", dest="process")
    options, args = op.parse_args()

    optionflag = 1
    if options.process:
        optionflag = 0
    if optionflag: op.error("incorrect options")

    if options.LogLevel:
        if options.LogLevel == 'CRITICAL': LogLevel = 50
        elif options.LogLevel == 'ERROR': LogLevel = 40
        elif options.LogLevel == 'WARNING': LogLevel = 30
        elif options.LogLevel == 'INFO': LogLevel = 20
        elif options.LogLevel == 'DEBUG': LogLevel = 10
        else: op.error("Invalid LogLevel")
        if LogLevel == 10: Debug = 1
        else: Debug = 0
    else:
        LogLevel = 20

    #Console = 1
    Console = 0

    if options.process:
        LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]
    else:
        LogFile = '/ESSArch/log/ESSlogging.log'
    ##########################
    # Log format
    MultiProc = 1
    if MultiProc:
        essFormatter1 = logging.Formatter('%(asctime)s %(name)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(name)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        #essFormatter1 = logging.Formatter('%(asctime)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        #essFormatter2 = logging.Formatter('%(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
    else:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
    ###########################
    # LocalFileHandler (main or root)
    LocalFileHandler_root = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_root.setLevel(LogLevel)
    LocalFileHandler_root.setFormatter(essFormatter1)
    ###########################
    # LocalFileHandler
    log_ProcName = 'AIPWriter'
    LogFile = ESSDB.DB().action('ESSProc','GET',('LogFile',),('Name',log_ProcName))[0][0]
    LogFile = LogFile[:-4] + '_2.log'
    LocalFileHandler_AIPWriter = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    #LocalFileHandler_AIPWriter = logging.handlers.TimedRotatingFileHandler(LogFile, when='M', interval=1, backupCount=1040)
    LocalFileHandler_AIPWriter.setLevel(LogLevel)
    LocalFileHandler_AIPWriter.setFormatter(essFormatter1)
    LocalFileHandler_AIPWriter.addFilter(nameFilter(log_ProcName))
    ###########################
    # LocalFileHandler
    log_ProcName = 'TLD'
    LogFile = ESSDB.DB().action('ESSProc','GET',('LogFile',),('Name',log_ProcName))[0][0]
    LogFile = LogFile[:-4] + '_2.log'
    LocalFileHandler_TLD = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_TLD.setLevel(LogLevel)
    LocalFileHandler_TLD.setFormatter(essFormatter1)
    LocalFileHandler_TLD.addFilter(nameFilter(log_ProcName))
    ###########################
    # LocalFileHandler
    log_ProcName = 'web_gui_index'
    LogFile = '/ESSArch/log/' + log_ProcName + '_2.log' 
    LocalFileHandler_web_gui_index = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_web_gui_index.setLevel(LogLevel)
    LocalFileHandler_web_gui_index.setFormatter(essFormatter1)
    LocalFileHandler_web_gui_index.addFilter(nameFilter(log_ProcName))
    ###########################
    # LocalFileHandler
    log_ProcName = 'web_gui_robot'
    LogFile = '/ESSArch/log/' + log_ProcName + '_2.log'
    LocalFileHandler_web_gui_robot = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    LocalFileHandler_web_gui_robot.setLevel(LogLevel)
    LocalFileHandler_web_gui_robot.setFormatter(essFormatter1)
    LocalFileHandler_web_gui_robot.addFilter(nameFilter(log_ProcName))
    ###########################
    # LocalConsoleHandler
    essConsoleHandler = logging.StreamHandler(sys.stdout)
    essConsoleHandler.setLevel(LogLevel)
    essConsoleHandler.setFormatter(essFormatter2)
    ##########################
    # Add handlers to default logger
    rootlogger = logging.getLogger('')
    rootlogger.setLevel(0)
    rootlogger.addHandler(LocalFileHandler_root)
    rootlogger.addHandler(LocalFileHandler_AIPWriter)
    rootlogger.addHandler(LocalFileHandler_TLD)
    rootlogger.addHandler(LocalFileHandler_web_gui_index)
    rootlogger.addHandler(LocalFileHandler_web_gui_robot)
    if Console:
        rootlogger.addHandler(essConsoleHandler)

    if options.process:
        tcpserver = LogRecordSocketReceiver()
        logging.info('About to start TCP server...')
        p1 = Process(target=tcpserver.serve_until_stopped)
        p1.start()
        while 1:
            Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('Time','Status','Run'),('Name',ProcName))[0]
            if Run == '0':
                logging.info('Stopping ' + ProcName)
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                p1.terminate()
                break
            time.sleep(10)
