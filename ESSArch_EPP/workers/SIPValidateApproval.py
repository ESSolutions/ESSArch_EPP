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

import sys, time, logging,  ESSDB, ESSPGM

from essarch.models import IngestQueue
from configuration.models import ArchivePolicy
from django import db

class Proc:
    ###############################################
    def ObjectValidate(self,InTable):
        self.IngestTable = InTable 
        if ExtDBupdate:
            self.ext_IngestTable = self.IngestTable
        else:
            self.ext_IngestTable = ''

        # Check if accepted in prjDB 
        self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectUUID','ObjectIdentifierValue','PolicyId','StatusProcess'),('StatusActivity','=','0','AND',
                                                                                                               'StatusProcess','BETWEEN',19,'AND',21))
        if errno: logging.error('Failed to access Local DB, error: ' + str(why))
        for self.obj in self.dbget:
            self.ObjectUUID = self.obj[0]
            self.ObjectIdentifierValue = self.obj[1]
            PolicyID = self.obj[2]
            self.StatusProcess = self.obj[3]
            ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1, PolicyID=PolicyID)[:1]
            if not ArchivePolicy_objs: 
                logging.error('Missing PolicyID: %s in db' % str(PolicyID))
            else:
                ArchivePolicy_obj = ArchivePolicy_objs.get()
                logging.info('StatusProcess %s, ObjectIdentifierValue %s, WaitForApproval: %s' % (self.StatusProcess,self.ObjectIdentifierValue,ArchivePolicy_obj.WaitProjectApproval))
                if ArchivePolicy_obj.WaitProjectApproval == 1:
                    #Check....
                    self.extOBJ = 0 
                    self.PrjDBget,errno,why = ESSDB.DB().action('ExtPrjDB','GET3',('DataObjectSize',
                                                                                   'DataObjectNumItems',
                                                                                   'Signature','Status'),
                                                                                  ('DataObjectIdentifier',self.ObjectIdentifierValue))
                    if errno: logging.error('Failed to access Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    if self.PrjDBget:
                        self.extOBJ = 1 
                        self.PrjDB_DataObjectSize=self.PrjDBget[0][0]	# not in use
                        self.PrjDB_DataObjectNumItems=self.PrjDBget[0][1]	# not in use
                        self.PrjDB_Signature=self.PrjDBget[0][2]		# not in use
                        self.PrjDB_Status=self.PrjDBget[0][3]
                        if self.PrjDB_Status == 1:
                            self.PrjAccepted = 1
                        elif self.PrjDB_Status == 0:
                            self.PrjAccepted = 0
                    else:
                        self.extOBJ = 0 
    
                    if not self.extOBJ: 
                        ###################################################################
                        #Object don't exist in prjDB(20) 
                        ###################################################################
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 20, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Change to StatusProcess 20, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                    elif self.extOBJ and not self.PrjAccepted: 
                        ###################################################################
                        #Object is not accepted in prjDB(21) 
                        ###################################################################
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 21, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Change to StatusProcess 21, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                    elif self.extOBJ and self.PrjAccepted: 
                        ###################################################################
                        #Object is accepted in prjDB(24) and RFNext and OK(0)
                        ###################################################################
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 24, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else: 
                            ESSPGM.Events().create('1020','','ESSArch SIPValidateApproval',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                        logging.info('Change to StatusProcess 24, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                elif ArchivePolicy_obj.WaitProjectApproval == 2:
                    ###################################################################
                    # Check if Object exist in ReqIngestQueue
                    ###################################################################
                    # id: INT
                    # ReqUUID: CHAR
                    # ReqType: INT
                    # ReqPurpose: VARCHAR
                    # user: VARCHAR
                    # password: VARCHAR
                    # ObjectIdentifierValue: VARCHAR
                    # Status: INT
                    # posted: DATETIME
#                    ReqIngestQueue_q = model.meta.Session.query(model.ReqIngestQueue)
#                    DbRow = ReqIngestQueue_q.filter(and_(model.ReqIngestQueue.ObjectIdentifierValue==self.ObjectIdentifierValue, \
#                                                         model.ReqIngestQueue.Status<=1)).first()
                    DbRow = IngestQueue.objects.filter( ObjectIdentifierValue=self.ObjectIdentifierValue, Status__lte=2 )[:1]
                    if DbRow:
                        DbRow = DbRow.get()
                        ###################################################################
                        #Object is accepted in ReqIngestQueue(24) and RFNext and OK(0)
                        ###################################################################
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 24, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else:
                            ESSPGM.Events().create('1020','','ESSArch SIPValidateApproval',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                            event_info = 'Start to Ingest SIP with ObjectIdentifierValue: %s, ReqUUID: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID)
                            logging.info(event_info)
                            ESSPGM.Events().create('1302',DbRow.ReqPurpose,'ESSArch Ingest',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                            DbRow.Status = 5
                            #model.meta.Session.commit()
                            DbRow.save()
                        logging.info('Change to StatusProcess 24, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                    else:
                        ###################################################################
                        #Object is not accepted in ReqIngestQueue(21)
                        ###################################################################
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 21, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Change to StatusProcess 21, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                    #model.meta.Session.close()
                else:
                    ###################################################################
                    #Skip Object check in ReqIngestQueue(24) and RFNext and OK(0)
                    ###################################################################
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 24, 0)
                    if errno:
                        logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    else: 
                        ESSPGM.Events().create('1020','','ESSArch SIPValidateApproval',ProcVersion,'0','Skip to check ReqIngestQueue',2,self.ObjectIdentifierValue)
                    logging.info('Skip check, Change to StatusProcess 24, ObjectIdentifierValue '+str(self.ObjectIdentifierValue))

#######################################################################################################
# Dep:
# Table: ESSProc with Name: ESSObjectValidate, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Table: ExtPrjDB with status from webservice "extobjectupdate"
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=0
    ProcName = 'SIPValidateApproval'
    ProcVersion = __version__
    if len(sys.argv) > 1: 
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0] 

    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
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

    logging.info('Starting ' + ProcName)
    while 1:
        #if Debug: logging.info('Check')
        InTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
        AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
        ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])
        #if Debug:
        #   logging.info('InTable: '+str(InTable))
        Proc().ObjectValidate(InTable)
        if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0] == '0': 
            ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
            logging.info('Stopping ' + ProcName)
            break
        db.close_old_connections()
        time.sleep(int(Time))
# ./SIPValidatexApproval.py 
