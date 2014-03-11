#!/usr/bin/env /ESSArch/pd/python/bin/python
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
import time, logging, sys, ESSDB
from pyftpdlib import ftpserver
from multiprocessing import Process

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

"""
Authorizer class: upon login users will be authenticated against the user
database created and maintained in django.
"""
class DjangoFtpAuthorizer:

    def has_user(self, username):
        try:
            u = User.objects.get(username = username)
            return True
        except:
            return False

    def get_home_dir(self, username):
        return '/Metadata'

    def get_msg_login(self, username):
        return 'Welcome to the ESSArch-FTP Server'

    def get_msg_quit(self, username):
        return 'Please come again'

    def r_perm(self, username, obj=None):
        try:
            return read_perms
        except:
            return False

    def w_perm(self, username, obj=None):
        try:
            return write_perms
        except:
            return False

    def has_perm(self, username, perm, path=None):
        u = User.objects.get(username = username)
        if u.has_perm('essarch.%s' % AgentIdentifierValue):
            if u.has_perm('essarch.add_ingestqueue'):
                return write_perms+read_perms
            elif u.has_perm('essarch.add_accessqueue'):
                return perm in read_perms
    
    def impersonate_user(self, username, password):
        """Impersonate another user (noop).

        It is always called before accessing the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to change the
        current user.
        """
        pass

    def terminate_impersonation(self, dummy):
        """Terminate impersonation (noop).

        It is always called after having accessed the filesystem.
        By default it does nothing.  The subclass overriding this
        method is expected to provide a mechanism to switch back
        to the original user.
        """
        pass

    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except:
            raise

    def validate_authentication(self, username, password):
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                return True
        return False

def create_ftpserver():
    ftpserver.log = logging.info
    ftpserver.logline = logging.debug
    ftpserver.logerror = logging.error
    # Instantiate a dummy authorizer for managing 'virtual' users
    #authorizer = ftpserver.DummyAuthorizer()

    # Define a new user having full r/w permissions
    #authorizer.add_user('meta', 'meta123', '/Metadata', perm='elradfmwM')

    # Instantiate FTP handler class
    handler = ftpserver.FTPHandler
    #handler.authorizer = authorizer
    handler.authorizer = DjangoFtpAuthorizer()

    # Define a customized banner (string returned when client connects)
    handler.banner = "ESSArch ftpd ready."

    # Instantiate FTP server class and listen on 0.0.0.0:21
    address = (FTP_ADDRESS, FTP_PORT)
    ftpd = ftpserver.FTPServer(address, handler)

    # set a limit for connections
    ftpd.max_cons = 256
    ftpd.max_cons_per_ip = 5

    return ftpd

def serve_ftpd(ftpd,ProcName):
    # start ftp server
    ftpd.serve_forever()

#######################################################################################################
# Dep:
# Table: ESSProc with Name: AIPPurge, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Table: ESSConfig with Name: PolicyTable Value: archpolicy
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'FTPServer'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]
    #LogLevel = logging.INFO
    LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 0
    Console = 0

    ##########################
    # Log format
    if MultiProc:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
    else:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
    ###########################
    # LocalFileHandler
    essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    essLocalFileHandler.setLevel(LogLevel)
    essLocalFileHandler.setFormatter(essFormatter1)
    #essLocalFileHandler.doRollover()
    ###########################
    # LocalConsoleHandler
    essConsoleHandler = logging.StreamHandler(sys.stdout)
    essConsoleHandler.setLevel(LogLevel)
    essConsoleHandler.setFormatter(essFormatter2)
    ##########################
    # Add handlers to default logger
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    logging = logging.getLogger('')
    logging.setLevel(0)
    logging.addHandler(essLocalFileHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        logging.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)

    logging.debug('LogFile: ' + str(LogFile))
    logging.debug('Time: ' + str(Time))
    logging.debug('Status: ' + str(Status))
    logging.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

    FTP_ADDRESS = '127.0.0.1'
    FTP_PORT = 2222
    read_perms = "elr"
    write_perms = "adfmw"

    ftpd = create_ftpserver()
    p = Process(target=serve_ftpd, args=(ftpd,ProcName))
    p.start()

    while 1:
        Time,Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
        if Run == '0':
            logging.info('Stopping ' + ProcName)
            ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
            p.terminate()
            break
        time.sleep(5)
