'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2016  ES Solutions AB

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
try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
else:
    __version__ = epp.__version__ 

from optparse import OptionParser

import ESSPGM,time,os,psutil

import django
django.setup()
from django.conf import settings
from configuration.models import ESSProc

def StartStop(action,ProcName=None):
    #processlist = ['ESSlogging', 'SIPReceiver', 'SIPValidateAIS', 'SIPValidateApproval', 'SIPValidateFormat', 'AIPCreator', 'AIPChecksum', 'AIPValidate', 'SIPRemove', 'TLD', 'AIPWriter', 'AIPPurge', 'AccessEngine', 'db_sync_ais', 'FTPServer']
    PROCESS_LIST = getattr(settings,'PROCESS_LIST',[])
    ProcName_dict = {}
    processlist = []
    for ProcName_full in PROCESS_LIST:
        ProcName_short = os.path.split(ProcName_full)[1].strip('.py')
        processlist.append(ProcName_short)
        ProcName_dict[ProcName_short] = ProcName_full
    ps_dict = get_ps_dict(PROCESS_LIST)
    
    if action in [1, 2]:
        processlist = [ProcName]
         
    #############################
    # Start process
    if action in [1, 3]:
        for ProcName in processlist:
            ps_objs = ps_dict[ProcName_dict[ProcName]]
            ESSProc_objs = ESSProc.objects.filter(Name=ProcName)
            if ESSProc_objs:
                ESSProc_obj = ESSProc_objs[0]
                if len(ps_objs) == 0:
                    if int(ESSProc_obj.Status) > 0:
                        print 'Process %s was not properly shutdown, try to start the process' % ProcName
                        ESSProc_obj.Status = 0
                        ESSProc_obj.save(update_fields=['Status'])
                    ESSPGM.PROC().action('Start',ProcName)     
                    loop_num = 0
                    time_range = range(0,121,5)
                    while 1:
                        ESSProc_obj.refresh_from_db()
                        if int(ESSProc_obj.Status) == 1:
                            print 'Process %s now running' % ProcName
                            break
                        elif int(ESSProc_obj.Status) == 0 and loop_num in time_range:
                            print 'Process %s not running' % ProcName
                        elif int(ESSProc_obj.Status) == 2:
                            print 'Process %s is going down' % ProcName
                        elif loop_num == time_range[-1]:
                            print 'Failed to start process %s' % ProcName
                            break
                        loop_num+=1
                        time.sleep(1)
                else:
                    print 'Process %s is already running' % ProcName
            else:
                print 'No database entry found for process: %s' % ProcName

    #############################
    # Stop process
    elif action in [2, 4]:
        processlist.reverse()
        for ProcName in processlist:
            ESSProc_objs = ESSProc.objects.filter(Name=ProcName)
            if ESSProc_objs:
                ESSProc_obj = ESSProc_objs[0]
                if int(ESSProc_obj.Status) in [1, 2]:
                    if int(ESSProc_obj.Status) == 1: 
                        ESSPGM.PROC().action('Stop',ProcName)
                    elif int(ESSProc_obj.Status) == 2: 
                        ESSPGM.PROC().action('Kill',ProcName)
                    loop_num = 0
                    time_range = range(0,601,5)
                    while 1:
                        ESSProc_obj.refresh_from_db()
                        ps_dict = get_ps_dict(PROCESS_LIST)
                        ps_objs = ps_dict[ProcName_dict[ProcName]]
                        if int(ESSProc_obj.Status) == 1 and loop_num in time_range:
                            print 'Process %s is still running' % ProcName
                        elif int(ESSProc_obj.Status) == 0:
                            print 'Process %s is stopped' % ProcName
                            break
                        elif int(ESSProc_obj.Status) == 2 and loop_num in time_range:
                            print 'Process %s is going down' % ProcName
                        
                        if loop_num == time_range[-1]:
                            print 'Failed to stop process %s' % ProcName
                            break
                        elif int(ESSProc_obj.Status) > 0 and len(ps_objs) == 0:
                            print 'Process %s was already stopped?' % ProcName
                            ESSProc_obj.Status = 0
                            ESSProc_obj.save(update_fields=['Status'])
                            break
                        loop_num+=1
                        time.sleep(1)                    
                else:
                    print 'Process %s is already stopped' % ProcName
            else:
                print 'No database entry found for process: %s' % ProcName

def get_ps_dict(process_list):
    """
    Count number of processes is running local server. Return a dict with processes.
    """
    process_dict = {}
    for process_item in process_list:
        process_dict[process_item] = []
    for p in psutil.process_iter():
        for process_item in process_list:
            if process_item in p.cmdline():
                process_dict[process_item].append(p)
    return process_dict

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


