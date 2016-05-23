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

import sys, os, datetime, time, logging, uuid, ESSDB, ESSMSSQL, ESSPGM, ESSlogging, ESSMD, pytz

from configuration.models import ArchivePolicy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django import db

################# Only for test ##################
disable_ObjectPackageName = 0
force_ProjectGroupCode = ''

class Proc:
    tz = timezone.get_default_timezone()
    ###############################################
    def ObjectValidate(self):
        self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0] 
        if ExtDBupdate:
            self.ext_IngestTable = self.IngestTable
        else:
            self.ext_IngestTable = ''

        # Check if exist extDB and got projektid
        self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue','PolicyID','StatusProcess','StatusActivity','ObjectUUID'),('StatusActivity','=','0','AND',
                                                                                                               'StatusProcess','BETWEEN',9,'AND',14,
                                                                                                               'OR',
                                                                                                               'StatusActivity','=','4','AND',
                                                                                                               'StatusProcess','BETWEEN',10,'AND',11))
        if errno: logging.error('Failed to access Local DB, error: ' + str(why))
        for self.obj in self.dbget:
            self.ObjectIdentifierValue = self.obj[0]
            self.PolicyID = self.obj[1]
            self.StatusProcess = self.obj[2]
            self.StatusActivity = self.obj[3]
            ObjectUUID = self.obj[4]
            self.DBmode = 0
            self.ext_ObjectGuid = ObjectUUID
            self.ext_EntryDate = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            self.ext_EntryAgentIdentifierValue = None
            self.ext_OAISPackageType = 2
            self.ext_preservationLevelValue = 1
            self.ext_ObjectActive = 0
            self.objectstatus = 0
            self.ext_ProjectGroupCode = ''
            self.ext_ObjectPackageName = ''
            if Debug: logging.info('StatusProcess 9, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
            #Check....
            if self.PolicyID:
                ArchivePolicy_objs = ArchivePolicy.objects.filter( PolicyStat = 1, PolicyID = str(self.PolicyID) )[:1]
                if ArchivePolicy_objs:
                    ArchivePolicy_obj = ArchivePolicy_objs.get()
                    if ArchivePolicy_obj.Mode in range(0,2):
                        self.DBmode = ArchivePolicy_obj.Mode
                        logging.info('Policy found for Object: %s in ESSArch mode' % self.ObjectIdentifierValue)
                        if ArchivePolicy_obj.IngestMetadata in [1,2,3]:
                            metsfilename = os.path.join(ArchivePolicy_obj.IngestPath,self.ObjectIdentifierValue + '_Package_METS.xml')
                        elif ArchivePolicy_obj.IngestMetadata in [4]:
                            ObjectPath = os.path.join(ArchivePolicy_obj.IngestPath,self.ObjectIdentifierValue)
                            if os.path.exists(os.path.join(ObjectPath,'sip.xml')):
                                metsfilename = os.path.join(ObjectPath,'sip.xml')
                            elif os.path.exists(os.path.join(ObjectPath,'mets.xml')):
                                metsfilename = os.path.join(ObjectPath,'mets.xml')
                            #elif os.path.exists(os.path.join(ObjectPath,'%s_Content_METS.xml' % self.ObjectIdentifierValue)):
                            #    metsfilename = os.path.join(ObjectPath,'%s_Content_METS.xml' % self.ObjectIdentifierValue)
                            else:
                                metsfilename = ''
                            #metsfilename = '%s/sip.xml' % os.path.join(ArchivePolicy_obj.IngestPath,self.ObjectIdentifierValue)
                        else:
                            metsfilename = ''
                        res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=metsfilename)
                        if not error:
                            # cut off microsecond and timezone info ".xxxxxxx+02:00" 
                            #for c in res_info[1][0]:
                            #    if c == '.' or c == '+':
                            #        break
                            #    else:
                            #        self.ext_EntryDate += c
                            self.ext_EntryDate = parse_datetime(res_info[1][0]).astimezone(pytz.utc)
                            self.ext_EntryAgentIdentifierValue = res_info[2][0][4]
                            try:
                                self.ext_ObjectGuid = str(uuid.UUID(self.ObjectIdentifierValue))
                            except ValueError, why:
                                logging.warning('ObjectIdentifierValue: %s is not a valid UUID, why: %s , start to generate a new UUID' % (self.ObjectIdentifierValue, str(why)))
                                self.ext_ObjectGuid = str(uuid.uuid1())
                                logging.info('New UUID: %s for ObjectIdentifierValue: %s' % (self.ext_ObjectGuid,str(self.ObjectIdentifierValue)))
                            self.ext_ObjectActive = 1
                            self.ext_OAISPackageType = 2
                            self.ext_preservationLevelValue = 1
                            self.objectstatus = 1
                        else:
                            self.objectstatus = 102 # Problem to get information from package METS 
                    elif ArchivePolicy_obj.Mode == 2: # AIS but POLICYID from METS, Check in AIS if object is active.
                        self.DBmode = ArchivePolicy_obj.Mode
                        self.extOBJdbget,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'GET3',('ProjectGroupCode',
                                                                                                           'ObjectPackageName',
                                                                                                           'ObjectGuid',
                                                                                                           'ObjectActive',
                                                                                                           'EntryDate',
                                                                                                           'EntryAgentIdentifierValue',
                                                                                                           'OAISPackageType',
                                                                                                           'preservationLevelValue'),
                                                                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        #self.extOBJdbget = [[10,'','7283074a-00c0-11e2-a78f-002215836500',1,'2010-07-12 16:57:45','entryagent',2,1]]
                        #ext_errno = 0
                        #ext_why = 'whywhy'
                        if ext_errno: logging.error('Failed to access External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                        elif self.extOBJdbget:
                            if Debug: logging.info('Found object: %s in AIS, self.extOBJdbget: %s',self.ObjectIdentifierValue,str(self.extOBJdbget))
                            self.objectstatus = 10 # Object found in external DB
                            if self.objectstatus < 100:
                                ########################################
                                # Check if object alredy have an AIP
                                if disable_ObjectPackageName:
                                    self.ext_ObjectPackageName = ''
                                else:
                                    self.ext_ObjectPackageName = self.extOBJdbget[0][1]
                                if not self.ext_ObjectPackageName:
                                    self.objectstatus = 12 # Object do not have an AIP
                                else:
                                    self.objectstatus = 112 # Object already have an AIP
                            if self.objectstatus < 100:
                                ########################################
                                # Get GUID/UUID
                                #self.ext_ObjectGuid = uuid.UUID(bytes_le=self.extOBJdbget[0][2])   #When pymssql
                                self.ext_ObjectGuid = uuid.UUID(self.extOBJdbget[0][2])
                            if self.objectstatus < 100:
                                ########################################
                                # Check if object is active
                                self.ext_ObjectActive = self.extOBJdbget[0][3]
                                if self.ext_ObjectActive == 1:
                                    self.objectstatus = 13 # Object is active
                                else:
                                    self.objectstatus = 113 # Object is not active
                            if self.objectstatus < 100:
                                ########################################
                                # Check if POLICYID in local DB "METS" is equal to ProjectGroupCode in AIS
                                self.ext_ProjectGroupCode = str(self.extOBJdbget[0][0])
                                if self.ext_ProjectGroupCode == self.PolicyID:
                                    self.objectstatus = 1 # Object have an ProjectCode
                                    logging.info('Object: %s found in AIS with correct POLICYID' % self.ObjectIdentifierValue)
                                else:
                                    self.objectstatus = 111 # Object do not have an ProjectCode
                            ########################################
                            self.ext_EntryDate = self.extOBJdbget[0][4].replace(microsecond=0,tzinfo=self.tz).astimezone(pytz.utc)
                            self.ext_EntryAgentIdentifierValue = self.extOBJdbget[0][5]
                            self.ext_OAISPackageType = self.extOBJdbget[0][6]
                            self.ext_preservationLevelValue = self.extOBJdbget[0][7]
                            ########################################
                            # Special function only for test
                            if force_ProjectGroupCode:
                                logging.info('Force set ProjectGroupCode for Object: %s' % self.ObjectIdentifierValue)
                                self.objectstatus = 10
                                self.ext_ProjectGroupCode = force_ProjectGroupCode
                                self.ext_ObjectPackageName = ''
                                self.ext_ObjectGuid = str(uuid.uuid1()) # updDB
                                self.ext_ObjectActive = 1 # updDB
                                self.ext_EntryDate = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc) # updDB
                                self.ext_EntryAgentIdentifierValue = None # updDB
                                self.ext_OAISPackageType = 2 # updDB
                                self.ext_preservationLevelValue = 1 # updDB
                        else:
                            self.objectstatus = 110 # Object not found in external DB
                            if Debug: logging.info('Missing object: %s in AIS, self.extOBJdbget: %s',self.ObjectIdentifierValue,str(self.extOBJdbget))
                    else:
                        self.objectstatus = 100 # Policy is not in ESSArch mode 
                else:
                    self.objectstatus = 101 # Policy not found or not active 
                #model.meta.Session.close()
            else: 
                self.DBmode = 2 # AIS 
                self.extOBJdbget,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'GET3',('ProjectGroupCode',
                                                                                                   'ObjectPackageName',
                                                                                                   'ObjectGuid',
                                                                                                   'ObjectActive',
                                                                                                   'EntryDate',
                                                                                                   'EntryAgentIdentifierValue',
                                                                                                   'OAISPackageType',
                                                                                                   'preservationLevelValue'),
                                                                                                  ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                if ext_errno: logging.error('Failed to access External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                elif self.extOBJdbget:
                #if not ext_errno and self.extOBJdbget:
                    if Debug: logging.info('Found object: %s in AIS, self.extOBJdbget: %s',self.ObjectIdentifierValue,str(self.extOBJdbget))
                    self.objectstatus = 10 # Object found in external DB
                    ########################################
                    # Check if object alredy have an AIP
                    self.ext_ProjectGroupCode = str(self.extOBJdbget[0][0])
                    if self.objectstatus < 100 and self.ext_ProjectGroupCode:
                        self.objectstatus = 11 # Object have an ProjectCode
                    else:
                        self.objectstatus = 111 # Object do not have an ProjectCode
                    ########################################
                    # Check if object alredy have an AIP
                    if disable_ObjectPackageName:
                        self.ext_ObjectPackageName = ''
                    else:
                        self.ext_ObjectPackageName = self.extOBJdbget[0][1]
                    if self.objectstatus < 100 and not self.ext_ObjectPackageName: 
                        self.objectstatus = 12 # Object do not have an AIP
                    else:
                        self.objectstatus = 112 # Object already have an AIP
                    ########################################
                    # Get GUID/UUID
                    #self.ext_ObjectGuid = uuid.UUID(bytes_le=self.extOBJdbget[0][2])	#When pymssql
                    self.ext_ObjectGuid = uuid.UUID(self.extOBJdbget[0][2])
                    ########################################
                    # Check if object is active
                    self.ext_ObjectActive = self.extOBJdbget[0][3]
                    if self.objectstatus < 100 and self.ext_ObjectActive == 1:
                        self.objectstatus = 13 # Object is active
                    else:
                        self.objectstatus = 113 # Object is not active

                    ########################################
                    self.ext_EntryDate = self.extOBJdbget[0][4].replace(microsecond=0,tzinfo=self.tz).astimezone(pytz.utc)
                    self.ext_EntryAgentIdentifierValue = self.extOBJdbget[0][5]
                    self.ext_OAISPackageType = self.extOBJdbget[0][6]
                    self.ext_preservationLevelValue = self.extOBJdbget[0][7]
                    if Debug: logging.info('ext_ProjectGroupCode is: '+str(self.ext_ProjectGroupCode)+' for ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
                    if force_ProjectGroupCode:
                        logging.info('Force set ProjectGroupCode for Object: %s' % self.ObjectIdentifierValue)
                        self.objectstatus = 10
                        self.ext_ProjectGroupCode = force_ProjectGroupCode
                        self.ext_ObjectPackageName = ''
                        self.ext_ObjectGuid = str(uuid.uuid1()) # updDB
                        self.ext_ObjectActive = 1 # updDB
                        self.ext_EntryDate = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc) # updDB
                        self.ext_EntryAgentIdentifierValue = None # updDB
                        self.ext_OAISPackageType = 2 # updDB
                        self.ext_preservationLevelValue = 1 # updDB
                    if self.objectstatus < 100:
                        ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1, AISProjectID=self.ext_ProjectGroupCode)[:1]
                        if ArchivePolicy_objs:
                            self.PolicyID = ArchivePolicy_objs.get().PolicyID
                            if Debug: logging.info('PolicyID: '+str(self.PolicyID))
                            self.objectstatus = 14 # Object got PolicyID
                        else:
                            self.objectstatus = 114 # Object mising PolicyID

                else:
                    self.objectstatus = 110 # Object not found in external DB
                    if Debug: logging.info('Missing object: %s in AIS, self.extOBJdbget: %s',self.ObjectIdentifierValue,str(self.extOBJdbget))

            if self.objectstatus == 100: # Policy is not in ESSArch mode
                ###################################################################
                # Policy is not in ESSArch mode(12) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 12
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 12, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Policy is not in ESSArch mode for Object: ' + str(self.ObjectIdentifierValue)
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 101: # Policy not found or not active
                ###################################################################
                # Policy not found or active(12) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 12
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 12, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Policy not found or active for Object: ' + str(self.ObjectIdentifierValue)
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 102: # Problem to get information from Package_METS
                ###################################################################
                # Problem to get information from Package_METS(12) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 12
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 12, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Problem to get information from Package_METS for Object: ' + str(self.ObjectIdentifierValue)
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 110:
                ###################################################################
                #Object don't exist in extDB(10) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 10
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 10, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))

            elif self.objectstatus == 111:
                ###################################################################
                #Object don't have any projektkod in extDB(11) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 11
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 11, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))

            elif self.objectstatus == 112:
                ###################################################################
                #Object already have an AIP!!
                ###################################################################
                self.StatusProcess = 13
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 13, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Object: ' + str(self.ObjectIdentifierValue) + ' already have an AIP!'
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 113:
                ###################################################################
                # Object is not active!!
                ###################################################################
                self.StatusProcess = 14
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 14, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Object: ' + str(self.ObjectIdentifierValue) + ' is not active in external DB!'
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 114: 
                ###################################################################
                #Object don't have any local policy(12) and Need of assistance(4)
                ###################################################################
                self.StatusProcess = 12
                self.StatusActivity = 4
                if Debug: logging.info('Change to StatusProcess 12, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                self.event_info = 'Object: ' + str(self.ObjectIdentifierValue) + ' do not have any local policy!'
                logging.error(self.event_info)
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)

            elif self.objectstatus == 14 or self.objectstatus == 1: 
                ###################################################################
                #Object got a policy(19) and RFNext and OK(0)
                ###################################################################
                self.StatusProcess = 19
                self.StatusActivity = 0
                if Debug: logging.info('Change to StatusProcess 19, ObjectIdentifierValue ' +str(self.ObjectIdentifierValue))
                ESSPGM.Events().create('1010','','ESSArch SIPValidateAIS',ProcVersion,'0','',self.DBmode,self.ObjectIdentifierValue)
        
            logging.info('objectstatus:%s,StatusProcess:%s,StatusActivity:%s,EntryDate:%s' % (self.objectstatus,self.StatusProcess,self.StatusActivity,self.ext_EntryDate))

            if self.objectstatus:
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('PolicyId',self.PolicyID,
                                                                          'ObjectUUID',self.ext_ObjectGuid,
                                                                          'EntryDate',self.ext_EntryDate.replace(tzinfo=None),
                                                                          'EntryAgentIdentifierValue',self.ext_EntryAgentIdentifierValue,
                                                                          'StatusProcess',self.StatusProcess,
                                                                          'StatusActivity',self.StatusActivity,
                                                                          'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                          'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                          'OAISPackageType',self.ext_OAISPackageType,
                                                                          'preservationLevelValue',self.ext_preservationLevelValue,
                                                                          'ObjectActive',self.ext_ObjectActive,
                                                                          'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                         ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                if errno == 0 and self.ext_IngestTable:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('PolicyId',self.PolicyID,
                                                                                             'StatusProcess',self.StatusProcess,
                                                                                             'StatusActivity',self.StatusActivity,
                                                                                             'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                             'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                            ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    if ext_errno: logging.error('Failed to update External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                    else:
                        res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))

#######################################################################################################
# Dep:
# Table: ESSProc with Name: ESSObjectValidate, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'SIPValidateAIS'
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
    #essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    essLocalFileHandler = logging.FileHandler(LogFile)
    essLocalFileHandler.setLevel(LogLevel)
    essLocalFileHandler.setFormatter(essFormatter1)
    #essLocalFileHandler.doRollover()
    ###########################
    # LocalConsoleHandler
    essConsoleHandler = logging.StreamHandler(sys.stdout)
    essConsoleHandler.setLevel(LogLevel)
    essConsoleHandler.setFormatter(essFormatter2)
    ###########################
    # SocketHandler
    essSocketHandler = ESSlogging.ESSSocketHandler('localhost',60100)
    ##########################
    # Add handlers to default logger
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    #logging = logging.getLogger('')
    esslogger = logging.getLogger('')
    #logging.setLevel(0)
    esslogger.setLevel(0)
    #logging.addHandler(essLocalFileHandler)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        #logging.addHandler(essConsoleHandler)
        esslogger.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

    logging.info('Starting ' + ProcName)
    while 1:
        #if Debug: logging.info('Check')
        Proc().ObjectValidate()
        if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0] == '0': 
            ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
            logging.info('Stopping ' + ProcName)
            break
        db.close_old_connections()
        time.sleep(int(Time))
# ./SIPValidateAIS.py 
