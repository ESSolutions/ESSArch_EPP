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
from optparse import OptionParser
import ESSPGM,ESSDB,time

def StartStop(action,ProcName=None):
    processlist = ['ESSlogging', 'SIPReceiver', 'SIPValidateAIS', 'SIPValidateApproval', 'SIPValidateFormat', 'AIPCreator', 'AIPChecksum', 'AIPValidate', 'SIPRemove', 'TLD', 'AIPWriter', 'AIPPurge', 'AccessEngine', 'db_sync_ais', 'FTPServer']
    #############################
    # Start process
    if action==1:
        procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
        if int(procstatus) == 0:
            ESSPGM.PROC().action('Start',ProcName)     
            time.sleep(1)
            while 1:
                procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
                if int(procstatus) == 1:
                    print 'Process ' + ProcName + ' now running'
                    break
                elif int(procstatus) == 0:
                    print 'Process ' + ProcName + ' not running'
                elif int(procstatus) == 2:
                    print 'Process ' + ProcName + ' is going down'
                time.sleep(2)
        else:
            print 'Process ' + ProcName + ' is already running'

    #############################
    # Stop process
    elif action==2:
        procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
        if int(procstatus) == 1 or int(procstatus) == 2:
            if int(procstatus) == 1: ESSPGM.PROC().action('Stop',ProcName)
            if int(procstatus) == 2: ESSPGM.PROC().action('Kill',ProcName)
            time.sleep(1)
            while 1:
                procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
                if int(procstatus) == 1:
                    print 'Process ' + ProcName + ' is still running'
                elif int(procstatus) == 0:
                    print 'Process ' + ProcName + ' is stopped'
                    break
                elif int(procstatus) == 2:
                    print 'Process ' + ProcName + ' is going down'
                time.sleep(2)
        else:
            print 'Process ' + ProcName + ' is already stopped'


    #############################
    # Start all process
    elif action==3:
        for ProcName in processlist:
            procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
            if int(procstatus) == 0:
                print 'Start process:', ProcName
                ESSPGM.PROC().action('Start',ProcName)
                time.sleep(1)
                while 1:
                    procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
                    if int(procstatus) == 1:
                        print 'Process ' + ProcName + ' now running'
                        break
                    elif int(procstatus) == 0:
                        print 'Process ' + ProcName + ' not running'
                    elif int(procstatus) == 2:
                        print 'Process ' + ProcName + ' is going down'
                    time.sleep(2)
            else:
                print 'Process ' + ProcName + ' is already running'

    #############################
    # Stop all process
    elif action==4:
        processlist.reverse()
        for ProcName in processlist:
            procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
            if int(procstatus) == 1 or int(procstatus) == 2:
                if int(procstatus) == 1:
                    print 'Stop process:', ProcName 
                    ESSPGM.PROC().action('Stop',ProcName)     
                elif int(procstatus) == 2:
                    print 'Kill process:', ProcName 
                    ESSPGM.PROC().action('Kill',ProcName)
                time.sleep(1)
                while 1:
                    procstatus = ESSDB.DB().action('ESSProc','GET',('Status',),('Name',ProcName))[0][0]
                    if int(procstatus) == 1:
                        print 'Process ' + ProcName + ' is still running'
                    elif int(procstatus) == 0:
                        print 'Process ' + ProcName + ' is stopped'
                        break
                    elif int(procstatus) == 2:
                        print 'Process ' + ProcName + ' is going down'
                    time.sleep(2)
            else:
                print 'Process ' + ProcName + ' is already stopped'

def main():
    op = OptionParser(usage="usage: %prog [options] arg", version="%prog 2.0")
    op.add_option("-u", "--up", help="Start process (NAME: SIPReceiver, SIPValidateAIS, SIPValidateApproval, SIPValidateFormat, AIPCreator, AIPChecksum, AIPValidate, SIPRemove, TLD, AIPWriter, AIPPurge, AccessEngine, db_sync_ais, ESSlogging, FTPServer)", dest="StartProcName", metavar="NAME")
    op.add_option("-d", "--down", help="Stop process (NAME: SIPReceiver, SIPValidateAIS, SIPValidateApproval, SIPValidateFormat, AIPCreator, AIPChecksum, AIPValidate, SIPRemove, TLD, AIPWriter, AIPPurge, AccessEngine, db_sync_ais, ESSlogging, FTPServer)", dest="StopProcName", metavar="NAME")
    op.add_option("-s", "--startALL", help="Start all process", action="store_true", dest="StartAllFlag")
    op.add_option("-q","--stopALL", help="Stop all process", action="store_true", dest="StopAllFlag")
    options, args = op.parse_args()

    if options.StartAllFlag:
        print 'Start All ESSArch process'
        StartStop(action=3)
    elif options.StopAllFlag:
        print 'Stop All ESSArch process'
        StartStop(action=4)
    elif options.StartProcName:
        print 'Start process:',options.StartProcName
        StartStop(action=1,ProcName=options.StartProcName)
    elif options.StopProcName:
        print 'Stop process:',options.StopProcName
        StartStop(action=2,ProcName=options.StopProcName)
    else:
        print 'Missing option'

if __name__ == "__main__":
    main()


