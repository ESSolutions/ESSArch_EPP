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
import os, thread, datetime, time, logging, sys, ESSDB, ESSPGM, ESSlogging, types, ESSMD, csv

from essarch.models import IngestQueue, ESSReg001, ArchiveObject
from django.db.models import Q
from django import db

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        #Remove Pause flag for ingest of new archive objects
        ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','SIPReceiver'))
        ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPCreator'))
        ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPChecksum'))
        ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPValidate'))
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0':
                logger.info('Stopping ' + ProcName)
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()
            self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
            if ExtDBupdate:
                self.ext_IngestTable = self.IngestTable
            else:
                self.ext_IngestTable = ''
            self.PolicyTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','PolicyTable'))[0][0]
            self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
            self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
            self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
            self.MediumLocation = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','storageMediumLocation'))[0][0]
            self.dbget_policyids,errno,why = ESSDB.DB().action(self.PolicyTable,'GET3',('PolicyID','Mode','AIPType',
                                                                                        'AIPpath','IngestMetadata',
                                                                                        'sm_1','sm_type_1','sm_format_1','sm_blocksize_1',
                                                                                        'sm_maxCapacity_1','sm_minChunkSize_1',
                                                                                        'sm_minContainerSize_1','sm_target_1',
                                                                                        'sm_2','sm_type_2','sm_format_2','sm_blocksize_2',
                                                                                        'sm_maxCapacity_2','sm_minChunkSize_2',
                                                                                        'sm_minContainerSize_2','sm_target_2',
                                                                                        'sm_3','sm_type_3','sm_format_3','sm_blocksize_3',
                                                                                        'sm_maxCapacity_3','sm_minChunkSize_3',
                                                                                        'sm_minContainerSize_3','sm_target_3',
                                                                                        'sm_4','sm_type_4','sm_format_4','sm_blocksize_4',
                                                                                        'sm_maxCapacity_4','sm_minChunkSize_4',
                                                                                        'sm_minContainerSize_4','sm_target_4'),
                                                                                       ('PolicyStat',1))
            if errno: logger.error('Failed to access Local DB, error: ' + str(why))
            for self.policyid_tuple in self.dbget_policyids:
                if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0]=='0':
                    logger.info('Stopping ' + ProcName)
                    ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                    #thread.interrupt_main()
                    break
                self.PolicyId = self.policyid_tuple[0]
                self.Mode = self.policyid_tuple[1]	#Not in use
                self.AIPType = self.policyid_tuple[2]	#Not in use
                self.AIPpath = self.policyid_tuple[3]
                self.metatype = self.policyid_tuple[4]
                self.sm_num = 0
                self.sm_list = []
                logger.debug('Start to list objects to write to storage method for policyid: ' + str(self.PolicyId))
                for self.sm in [(self.policyid_tuple[5],self.policyid_tuple[6],self.policyid_tuple[7],self.policyid_tuple[8],
                                self.policyid_tuple[9],self.policyid_tuple[10],self.policyid_tuple[11],self.policyid_tuple[12]),
                               (self.policyid_tuple[13],self.policyid_tuple[14],self.policyid_tuple[15],self.policyid_tuple[16],
                                self.policyid_tuple[17],self.policyid_tuple[18],self.policyid_tuple[19],self.policyid_tuple[20]),
                               (self.policyid_tuple[21],self.policyid_tuple[22],self.policyid_tuple[23],self.policyid_tuple[24],
                                self.policyid_tuple[25],self.policyid_tuple[26],self.policyid_tuple[27],self.policyid_tuple[28]),
                               (self.policyid_tuple[29],self.policyid_tuple[30],self.policyid_tuple[31],self.policyid_tuple[32],
                                self.policyid_tuple[33],self.policyid_tuple[34],self.policyid_tuple[35],self.policyid_tuple[36])]:
                    self.sm_num += 1
                    # Check if PolicyID is active (1)
                    if self.sm[0] == 1:
                        self.sm_type = self.sm[1]
                        self.sm_format = self.sm[2]
                        self.sm_blocksize = self.sm[3]
                        self.sm_maxCapacity = self.sm[4]
                        self.sm_minChunkSize = self.sm[5]
                        self.sm_minContainerSize = self.sm[6]
                        self.sm_target = self.sm[7]
                        self.sm_location = self.MediumLocation
                        self.sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location]
                        # Check if policyid has enough Objects "totalt ObjectSize" to be written to storage method
                        self.ObjectSizeSum = ESSDB.DB().action(self.IngestTable,'GETsum',('ObjectSize',),('PolicyId','=',self.PolicyId,'AND',
                                                                                                          'StatusProcess','BETWEEN',69,'AND',1000,'AND',
                                                                                                          '(StatusActivity','BETWEEN',5,'AND',6,'OR',
                                                                                                          'StatusActivity','=',0,')'))
                        if self.ObjectSizeSum:
                            if type(self.ObjectSizeSum[0][0]) is not types.NoneType:
                                self.ObjectSizeSum = int(self.ObjectSizeSum[0][0])
                            else:
                                self.ObjectSizeSum = 0
                        else:
                            self.ObjectSizeSum = 0
                        if int(self.sm_minChunkSize) < self.ObjectSizeSum:
                            self.sm_minChunkSize_flag = 1
                        else:
                            self.sm_minChunkSize_flag = 0
                        logging.info('PolicyId: %s, sm_num: %s, sm_minChunkSize_flag: %s, sm_minChunkSize: %s, ObjectSizeSum: %s' % (str(self.PolicyId),str(self.sm_num),str(self.sm_minChunkSize_flag),str(self.sm_minChunkSize),str(self.ObjectSizeSum)))
                        ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = self.PolicyId),
                                                                          Q(StatusProcess__range = [69,1000]),
                                                                          Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                                          )
#                        self.dbget_objects,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue',
#                                                                                                  'ObjectUUID',
#                                                                                                  'MetaObjectIdentifier',
#                                                                                                  'MetaObjectSize',
#                                                                                                  'DataObjectSize',
#                                                                                                  'ObjectPackageName',
#                                                                                                  'ObjectSize',
#                                                                                                  'DataObjectNumItems',
#                                                                                                  'StatusProcess',
#                                                                                                  'StatusActivity'),
#                                                                                                 ('PolicyId','=',self.PolicyId,'AND',
#                                                                                                  'StatusProcess','BETWEEN',69,'AND',1000,'AND',
#                                                                                                  '(','StatusActivity','BETWEEN',5,'AND',6,'OR',
#                                                                                                  'StatusActivity','=',0,')'))
#                        if errno: logger.error('Failed to access Local DB, error: ' + str(why))
#                        self.numobjects = len(self.dbget_objects)
#                        for self.obj in self.dbget_objects:
                        self.numobjects = ArchiveObject_objs.count()
                        for ArchiveObject_obj in ArchiveObject_objs:
                            if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0]=='0':
                                logger.info('Stopping ' + ProcName)
                                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                                #thread.interrupt_main()
                                time.sleep(10)
                                break
                            self.ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
                            self.ObjectUUID = ArchiveObject_obj.ObjectUUID
                            self.Pmets_objpath = os.path.join(self.AIPpath,self.ObjectIdentifierValue + '_Package_METS.xml')
                            self.MetaObjectSize = os.stat(self.Pmets_objpath)[6]
                            #self.MetaObjectSize = int(ArchiveObject_obj.MetaObjectSize)
                            self.DataObjectSize = int(ArchiveObject_obj.DataObjectSize)
                            self.ObjectPackageName = ArchiveObject_obj.ObjectPackageName
                            self.ObjectSize = int(ArchiveObject_obj.ObjectSize)
                            self.DataObjectNumItems = ArchiveObject_obj.DataObjectNumItems
                            self.StatusProcess = int(ArchiveObject_obj.StatusProcess)
                            self.StatusActivity = int(ArchiveObject_obj.StatusActivity)
                            self.ESSReg001,errno,why = ESSDB.DB().action('ESSReg001','GET3',('i001', 'i010', 'i011', 'i012', 'i013', 
                                                                                             's010', 's011', 's012', 's013'), 
                                                                                            ('ObjectUUID',self.ObjectUUID))
                            if errno: logger.error('Failed to access Local DB, error: ' + str(why))
                            if self.ESSReg001:
                                self.ESSReg001_i001=int(self.ESSReg001[0][0])
                                self.ESSReg001_i010=int(self.ESSReg001[0][1])
                                self.ESSReg001_i011=int(self.ESSReg001[0][2])
                                self.ESSReg001_i012=int(self.ESSReg001[0][3])
                                self.ESSReg001_i013=int(self.ESSReg001[0][4])
                                self.ESSReg001_s010=self.ESSReg001[0][5]
                                self.ESSReg001_s011=self.ESSReg001[0][6]
                                self.ESSReg001_s012=self.ESSReg001[0][7]
                                self.ESSReg001_s013=self.ESSReg001[0][8]
                            else:
                                self.ESSReg001_i001=self.PolicyId
                                self.ESSReg001_i010=0
                                self.ESSReg001_i011=0
                                self.ESSReg001_i012=0
                                self.ESSReg001_i013=0
                                self.ESSReg001_s010=''
                                self.ESSReg001_s011=''
                                self.ESSReg001_s012=''
                                self.ESSReg001_s013=''
                                ESSReg001_obj = ESSReg001()
                                ESSReg001_obj.ObjectUUID = ArchiveObject_obj
                                ESSReg001_obj.i001 = self.ESSReg001_i001
                                ESSReg001_obj.i010 = self.ESSReg001_i010
                                ESSReg001_obj.i011 = self.ESSReg001_i011
                                ESSReg001_obj.i012 = self.ESSReg001_i012
                                ESSReg001_obj.i013 = self.ESSReg001_i013
                                ESSReg001_obj.s010 = self.ESSReg001_s010
                                ESSReg001_obj.s011 = self.ESSReg001_s011
                                ESSReg001_obj.s012 = self.ESSReg001_s012
                                ESSReg001_obj.s013 = self.ESSReg001_s013
                                ESSReg001_obj.save() 
                                #res,errno,why = ESSDB.DB().action('ESSReg001','INS',('ObjectUUID',self.ObjectUUID,
                                #                                                     'i001',self.ESSReg001_i001,
                                #                                                     'i010',self.ESSReg001_i010,
                                #                                                     'i011',self.ESSReg001_i011,
                                #                                                     'i012',self.ESSReg001_i012,
                                #                                                     'i013',self.ESSReg001_i013,
                                #                                                     's010',self.ESSReg001_s010,
                                #                                                     's011',self.ESSReg001_s011,
                                #                                                     's012',self.ESSReg001_s012,
                                #                                                     's013',self.ESSReg001_s013))
                                #if errno: logger.error('Failed to insert to Local DB, error: ' + str(why))
                            ############################################################
                            # Storage Method 1
                            if self.sm_num == 1:
                                if self.ESSReg001_i010==0 or self.ESSReg001_i010==1:
                                    if self.sm_minChunkSize_flag == 1:
                                        #if (self.StatusProcess==69 and self.StatusActivity==0) or (self.StatusProcess==1000 and self.StatusActivity==6):
                                        if self.StatusProcess==69 and self.StatusActivity==0:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 5)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ReqUUID,errno,why = ESSPGM.DB().CreateWriteReq(self.AIPpath, self.ObjectUUID, self.ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
                                        if errno:
                                            logger.error('Problem to Create WriteReq for Object: ' + str(self.ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + str(why))
                                            time.sleep(1)
                                            thread.interrupt_main()
                                            break
                                        logger.info('Add WriteReq with storage method type: ' + str(self.sm_type) + ' for object: ' + self.ObjectIdentifierValue + ' IO_uuid: ' + str(self.ReqUUID))
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s010',self.ReqUUID,
                                                                                             'i010',2),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                    else:
                                        if self.StatusProcess==69 and self.StatusActivity==0:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 6)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        if self.ESSReg001_i010==0:
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s010','',
                                                                                                 'i010',1),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                elif self.ESSReg001_i010==2 or self.ESSReg001_i010==4:
                                    self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s010))
                                    if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s010,self.ObjectIdentifierValue,str(why))
                                    elif self.res_ioqueue:
                                        self.IOstatus = int(self.res_ioqueue[0][0])
                                        if self.IOstatus == 20:
                                            self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s010) + ' for: ' + str(self.ObjectIdentifierValue)
                                            logger.info(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i010',3),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        elif self.IOstatus > 20:
                                            self.event_info = 'Problem for WriteReq IO_uuid: ' + str(self.ESSReg001_s010) + ' for: ' + self.ObjectIdentifierValue
                                            logger.error(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i010',4),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 4)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            logger.info('After critical error try to stop ' + ProcName)
                                            ESSDB.DB().action('ESSProc','UPD',('Run','0'),('Name',ProcName))

                            ############################################################
                            # Storage Method 2
                            elif self.sm_num == 2:
                                if self.ESSReg001_i011==0 or self.ESSReg001_i011==1:
                                    if self.sm_minChunkSize_flag == 1:
                                        if self.StatusProcess==1000 and self.StatusActivity==6:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 5)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ReqUUID,errno,why = ESSPGM.DB().CreateWriteReq(self.AIPpath, self.ObjectUUID, self.ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
                                        if errno:
                                            logger.error('Problem to Create WriteReq for Object: ' + str(self.ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + str(why))
                                            time.sleep(1)
                                            thread.interrupt_main()
                                            break
                                        logger.info('Add WriteReq with storage method type: ' + str(self.sm_type) + ' for object: ' + self.ObjectIdentifierValue + ' IO_uuid: ' + str(self.ReqUUID))
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s011',self.ReqUUID,
                                                                                             'i011',2),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                    else:
                                        if self.StatusProcess==1000 and self.StatusActivity==5:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 6)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        if self.ESSReg001_i011==0:
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s011','',
                                                                                                 'i011',1),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                elif self.ESSReg001_i011==2 or self.ESSReg001_i011==4:
                                    self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s011))
                                    if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s011,self.ObjectIdentifierValue,str(why))
                                    elif self.res_ioqueue:
                                        self.IOstatus = int(self.res_ioqueue[0][0])
                                        if self.IOstatus == 20:
                                            self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s011) + ' for: ' + str(self.ObjectIdentifierValue)
                                            logger.info(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i011',3),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        elif self.IOstatus > 20:
                                            self.event_info = 'Problem for WriteReq IO_uuid: ' + str(self.ESSReg001_s011) + ' for: ' + self.ObjectIdentifierValue
                                            logger.error(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i011',4),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 4)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            logger.info('After critical error try to stop ' + ProcName)
                                            ESSDB.DB().action('ESSProc','UPD',('Run','0'),('Name',ProcName))

                            ############################################################
                            # Storage Method 3
                            elif self.sm_num == 3:
                                if self.ESSReg001_i012==0 or self.ESSReg001_i012==1:
                                    if self.sm_minChunkSize_flag == 1:
                                        if self.StatusProcess==1000 and self.StatusActivity==6:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 5)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ReqUUID,errno,why = ESSPGM.DB().CreateWriteReq(self.AIPpath, self.ObjectUUID, self.ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
                                        if errno:
                                            logger.error('Problem to Create WriteReq for Object: ' + str(self.ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + str(why))
                                            time.sleep(1)
                                            thread.interrupt_main()
                                            break
                                        logger.info('Add WriteReq with storage method type: ' + str(self.sm_type) + ' for object: ' + self.ObjectIdentifierValue + ' IO_uuid: ' + str(self.ReqUUID))
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s012',self.ReqUUID,
                                                                                             'i012',2),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                    else:
                                        if self.StatusProcess==1000 and self.StatusActivity==5:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 6)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        if self.ESSReg001_i012==0:
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s012','',
                                                                                                 'i012',1),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                elif self.ESSReg001_i012==2 or self.ESSReg001_i012==4:
                                    self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s012))
                                    if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s012,self.ObjectIdentifierValue,str(why))
                                    elif self.res_ioqueue:
                                        self.IOstatus = int(self.res_ioqueue[0][0])
                                        if self.IOstatus == 20:
                                            self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s012) + ' for: ' + str(self.ObjectIdentifierValue)
                                            logger.info(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i012',3),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        elif self.IOstatus > 20:
                                            self.event_info = 'Problem for WriteReq IO_uuid: ' + str(self.ESSReg001_s012) + ' for: ' + self.ObjectIdentifierValue
                                            logger.error(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i012',4),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 4)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            logger.info('After critical error try to stop ' + ProcName)
                                            ESSDB.DB().action('ESSProc','UPD',('Run','0'),('Name',ProcName))

                            ############################################################
                            # Storage Method 4
                            elif self.sm_num == 4:
                                if self.ESSReg001_i013==0 or self.ESSReg001_i013==1:
                                    if self.sm_minChunkSize_flag == 1:
                                        if self.StatusProcess==1000 and self.StatusActivity==6:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 5)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ReqUUID,errno,why = ESSPGM.DB().CreateWriteReq(self.AIPpath, self.ObjectUUID, self.ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
                                        if errno:
                                            logger.error('Problem to Create WriteReq for Object: ' + str(self.ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + str(why))
                                            time.sleep(1)
                                            thread.interrupt_main()
                                            break
                                        logger.info('Add WriteReq with storage method type: ' + str(self.sm_type) + ' for object: ' + self.ObjectIdentifierValue + ' IO_uuid: ' + str(self.ReqUUID))
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s013',self.ReqUUID,
                                                                                             'i013',2),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                    else:
                                        if self.StatusProcess==1000 and self.StatusActivity==5:
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 6)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        if self.ESSReg001_i013==0:
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('s013','',
                                                                                                 'i013',1),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                elif self.ESSReg001_i013==2 or self.ESSReg001_i013==4:
                                    self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s013))
                                    if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s013,self.ObjectIdentifierValue,str(why))
                                    elif self.res_ioqueue:
                                        self.IOstatus = int(self.res_ioqueue[0][0])
                                        if self.IOstatus == 20:
                                            self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s013) + ' for: ' + str(self.ObjectIdentifierValue)
                                            logger.info(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i013',3),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        elif self.IOstatus > 20:
                                            self.event_info = 'Problem for WriteReq IO_uuid: ' + str(self.ESSReg001_s013) + ' for: ' + self.ObjectIdentifierValue
                                            logger.error(self.event_info)
                                            ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                            res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i013',4),
                                                                                                ('ObjectUUID',self.ObjectUUID))
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 4)
                                            if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                            logger.info('After critical error try to stop ' + ProcName)
                                            ESSDB.DB().action('ESSProc','UPD',('Run','0'),('Name',ProcName))
                ############################################################
                # Check if write is done to all Storage Methods for AIPs
                time.sleep(1)
                ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = self.PolicyId),
                                                                  Q(StatusProcess = 1000),
                                                                  Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                                  )
#                self.dbget_objects,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue',
#                                                                                          'ObjectUUID',
#                                                                                          'MetaObjectIdentifier',
#                                                                                          'MetaObjectSize',
#                                                                                          'DataObjectSize',
#                                                                                          'ObjectPackageName',
#                                                                                          'ObjectSize',
#                                                                                          'DataObjectNumItems',
#                                                                                          'StatusProcess',
#                                                                                          'StatusActivity'),
#                                                                                         ('PolicyId','=',self.PolicyId,'AND',
#                                                                                          'StatusProcess','=',1000,'AND',
#                                                                                          '(','StatusActivity','BETWEEN',5,'AND',6,'OR',
#                                                                                          'StatusActivity','=',0,')'))
#                if errno: logger.error('Failed to access Local DB, error: ' + str(why))
#                self.numobjects = len(self.dbget_objects)
#                for self.obj in self.dbget_objects:
                self.numobjects = ArchiveObject_objs.count()
                for ArchiveObject_obj in ArchiveObject_objs:
                    if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0]=='0':
                        logger.info('Stopping ' + ProcName)
                        ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                        #thread.interrupt_main()
                        time.sleep(10)
                        break
                    self.ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
                    self.ObjectUUID = ArchiveObject_obj.ObjectUUID
                    self.MetaObjectSize = ArchiveObject_obj.MetaObjectSize
                    self.DataObjectSize = ArchiveObject_obj.DataObjectSize
                    self.ObjectPackageName = ArchiveObject_obj.ObjectPackageName
                    self.ObjectSize = ArchiveObject_obj.ObjectSize
                    self.DataObjectNumItems = ArchiveObject_obj.DataObjectNumItems
                    self.StatusProcess = ArchiveObject_obj.StatusProcess
                    self.StatusActivity = ArchiveObject_obj.StatusActivity
#                    self.ObjectIdentifierValue = self.obj[0]
#                    self.ObjectUUID = self.obj[1]
#                    self.MetaObjectSize = self.obj[3]
#                    self.DataObjectSize = self.obj[4]
#                    self.ObjectPackageName = self.obj[5]
#                    self.ObjectSize = self.obj[6]
#                    self.DataObjectNumItems = self.obj[7]
#                    self.StatusProcess = self.obj[8]
#                    self.StatusActivity = self.obj[9]
                    #logger.info('Check if object is done, self.obj: ' + str(self.obj))
                    self.ESSReg001,errno,why = ESSDB.DB().action('ESSReg001','GET3',('i001', 'i010', 'i011', 'i012', 'i013',
                                                                                     's010', 's011', 's012', 's013'),
                                                                                    ('ObjectUUID',self.ObjectUUID))
                    if errno: logger.error('Failed to access Local DB, error: ' + str(why))
                    if self.ESSReg001:
                        self.ESSReg001_i001=int(self.ESSReg001[0][0])
                        self.ESSReg001_i010=int(self.ESSReg001[0][1])
                        self.ESSReg001_i011=int(self.ESSReg001[0][2])
                        self.ESSReg001_i012=int(self.ESSReg001[0][3])
                        self.ESSReg001_i013=int(self.ESSReg001[0][4])
                        self.ESSReg001_s010=self.ESSReg001[0][5]
                        self.ESSReg001_s011=self.ESSReg001[0][6]
                        self.ESSReg001_s012=self.ESSReg001[0][7]
                        self.ESSReg001_s013=self.ESSReg001[0][8]
                        if self.ESSReg001_i010==3 and (self.ESSReg001_i011==0 or self.ESSReg001_i011==3) and (self.ESSReg001_i012==0 or self.ESSReg001_i012==3) and (self.ESSReg001_i013==0 or self.ESSReg001_i013==3):
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1999, 0)
                            if errno == 0 or errno == '08S01': 
                                if errno == '08S01':
                                    logger.warning('Failed to update central DB status for AIPB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                self.event_info = 'Succedd to write AIP: %s to all Storage Methods (%s,%s,%s,%s)' % (self.ObjectIdentifierValue,str(self.ESSReg001_i010),str(self.ESSReg001_i011),str(self.ESSReg001_i012),str(self.ESSReg001_i013))
                                logger.info(self.event_info)
                                ESSPGM.Events().create('1100','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                ESSDB.DB().action('ESSReg001','DEL',('ObjectUUID',self.ObjectUUID))
                                if len(self.ESSReg001_s010): ESSDB.DB().action('IOqueue','DEL',('work_uuid',self.ESSReg001_s010))
                                if len(self.ESSReg001_s011): ESSDB.DB().action('IOqueue','DEL',('work_uuid',self.ESSReg001_s011))
                                if len(self.ESSReg001_s012): ESSDB.DB().action('IOqueue','DEL',('work_uuid',self.ESSReg001_s012))
                                if len(self.ESSReg001_s013): ESSDB.DB().action('IOqueue','DEL',('work_uuid',self.ESSReg001_s013))
                                #################################
                                # Complete Ingest Order
                                DbRow = IngestQueue.objects.filter( ObjectIdentifierValue=self.ObjectIdentifierValue, Status=5 )[:1]
                                if DbRow:
                                    DbRow = DbRow.get()
                                    event_info = 'Succeeded to Ingest SIP with ObjectIdentifierValue: %s, ReqUUID: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID)
                                    logger.info(event_info)
                                    ESSPGM.Events().create('1303',DbRow.ReqPurpose,'ESSArch Ingest',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                                    DbRow.Status = 20
                                    DbRow.save()
                                ##################################################################
                                # Special solution for MKC projectDB feedback
                                self.UpdateExtPrjDB = 0
                                self.ExtPrjTapedURL = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtPrjTapedURL'))
                                if self.ExtPrjTapedURL:
                                    if len(self.ExtPrjTapedURL[0][0]):
                                        self.UpdateExtPrjDB = 1
                                if self.UpdateExtPrjDB:
                                    # Update ExtPrjDB
                                    self.date = datetime.datetime.today().strftime("%Y-%m-%d")
                                    self.time = datetime.datetime.today().strftime("%H:%M:%S")
                                    self.StorageTableDB,errno,why = ESSDB.DB().action(self.StorageTable,'GET3',('contentLocationValue','storageMediumID'),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                    if errno: logger.error('Failed to access Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                    ESSPGM.ExtPrjDB().taped(self.ObjectIdentifierValue,self.DataObjectNumItems,self.DataObjectSize,self.date,self.time,self.StorageTableDB[0][1],self.StorageTableDB[1][1],self.StorageTableDB[0][0],self.StorageTableDB[1][0])
                                if self.metatype == 1: # METS
                                    # Get SIP Content METS information
                                    self.RECEIPT_EMAIL = ''
                                    self.Pmets_objpath = os.path.join(self.AIPpath,self.ObjectIdentifierValue + '_Package_METS.xml')
                                    res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=self.Pmets_objpath)
                                    for agent in res_info[2]:
                                        if agent[0] == 'PRESERVATION' and \
                                           agent[2] == 'OTHER' and \
                                           agent[3] == 'SOFTWARE' and \
                                           agent[4] == 'ESSArch':
                                            note = csv.reader(agent[5], delimiter='=')
                                            for i in note:
                                                if i[0] == 'RECEIPT_EMAIL':
                                                    self.RECEIPT_EMAIL = i[1]
                                    if self.RECEIPT_EMAIL:
                                        self.smtp_server = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','smtp_server'))[0][0]
                                        if self.smtp_server:         
                                            self.email_from = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','email_from'))[0][0]
                                            logger.info('Sending receipt to email address: %s for AIP: %s' % (self.RECEIPT_EMAIL,self.ObjectIdentifierValue))
                                            ESSPGM.mail().send(self.email_from,self.RECEIPT_EMAIL,u'ESSArch receipt - object "%s" successfully archived!' % self.ObjectIdentifierValue,u'Object "%s" was successfully archived and can now be accessed from ESSArch.\n\nPlease return to "ESSArch Client" and click on menu "Access" to access archived objects.' % self.ObjectIdentifierValue,smtp_server=self.smtp_server,smtp_timeout=30)
                                        else:
                                            logger.warning('smtp_server not configured, skip to send email receipt for AIP: %s' % self.ObjectIdentifierValue)
                                    else:
                                        logger.error('Missing receipt email address for AIP: %s' % self.ObjectIdentifierValue)
                            else: 
                                logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        elif self.ESSReg001_i010==4 or self.ESSReg001_i011==4 or self.ESSReg001_i012==4 or self.ESSReg001_i013==4:
                            if self.ESSReg001_i010==4:
                                self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s010))
                                if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s010,self.ObjectIdentifierValue,str(why))
                                elif self.res_ioqueue:
                                    self.IOstatus = int(self.res_ioqueue[0][0])
                                    if self.IOstatus == 20:
                                        self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s010) + ' for: ' + str(self.ObjectIdentifierValue)
                                        logger.info(self.event_info)
                                        ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i010',3),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                        if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ESSReg001_i010==3
                            if self.ESSReg001_i011==4:
                                self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s011))
                                if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s011,self.ObjectIdentifierValue,str(why))
                                elif self.res_ioqueue:
                                    self.IOstatus = int(self.res_ioqueue[0][0])
                                    if self.IOstatus == 20:
                                        self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s011) + ' for: ' + str(self.ObjectIdentifierValue)
                                        logger.info(self.event_info)
                                        ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i011',3),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                        if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ESSReg001_i011==3
                            if self.ESSReg001_i012==4:
                                self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s012))
                                if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s012,self.ObjectIdentifierValue,str(why))
                                elif self.res_ioqueue:
                                    self.IOstatus = int(self.res_ioqueue[0][0])
                                    if self.IOstatus == 20:
                                        self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s012) + ' for: ' + str(self.ObjectIdentifierValue)
                                        logger.info(self.event_info)
                                        ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i012',3),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                        if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ESSReg001_i012==3
                            if self.ESSReg001_i013==4:
                                self.res_ioqueue,errno,why=ESSDB.DB().action('IOqueue','GET3',('Status',),('work_uuid',self.ESSReg001_s013))
                                if errno: logger.error('Problem to get status for WriteReq: %s for AIP: %s error: %s',self.ESSReg001_s013,self.ObjectIdentifierValue,str(why))
                                elif self.res_ioqueue:
                                    self.IOstatus = int(self.res_ioqueue[0][0])
                                    if self.IOstatus == 20:
                                        self.event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ESSReg001_s013) + ' for: ' + str(self.ObjectIdentifierValue)
                                        logger.info(self.event_info)
                                        ESSPGM.Events().create('1101','','ESSArch AIPWriter',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                                        res,errno,why = ESSDB.DB().action('ESSReg001','UPD',('i013',3),
                                                                                            ('ObjectUUID',self.ObjectUUID))
                                        if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                        self.ESSReg001_i013==3
                            if self.ESSReg001_i010==4 or self.ESSReg001_i011==4 or self.ESSReg001_i012==4 or self.ESSReg001_i013==4:
                                self.event_info = 'Problem to write AIP: %s to all Storage Methods (%s,%s,%s,%s)' % (self.ObjectIdentifierValue,str(self.ESSReg001_i010),str(self.ESSReg001_i011),str(self.ESSReg001_i012),str(self.ESSReg001_i013))
                                logger.error(self.event_info)
                                ESSPGM.Events().create('1100','','ESSArch AIPWriter',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 1000, 4)
                                if errno: logger.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else:
                            logger.info('Pending writes for AIP: %s to Storage Methods (%s,%s,%s,%s)',self.ObjectIdentifierValue,str(self.ESSReg001_i010),str(self.ESSReg001_i011),str(self.ESSReg001_i012),str(self.ESSReg001_i013))
            ############################################################################
            # Check if any active Write IO exist and then pause Ingest of new ojects
            self.ESSReg001,errno,why = ESSDB.DB().action('ESSReg001','GET3',('i001', 'i010', 'i011', 'i012', 'i013',
                                                                             's010', 's011', 's012', 's013'))
            if errno: logger.error('Failed to access Local DB, error: ' + str(why))
            self.PauseFlag = 0
            for self.ESSReg001row in self.ESSReg001: 
                self.ESSReg001_i001=int(self.ESSReg001row[0])
                self.ESSReg001_i010=int(self.ESSReg001row[1])
                self.ESSReg001_i011=int(self.ESSReg001row[2])
                self.ESSReg001_i012=int(self.ESSReg001row[3])
                self.ESSReg001_i013=int(self.ESSReg001row[4])
                self.ESSReg001_s010=self.ESSReg001row[5]
                self.ESSReg001_s011=self.ESSReg001row[6]
                self.ESSReg001_s012=self.ESSReg001row[7]
                self.ESSReg001_s013=self.ESSReg001row[8]
                if self.ESSReg001_i010==2 or self.ESSReg001_i011==2 or self.ESSReg001_i012==2 or self.ESSReg001_i013==2:
                    self.PauseFlag = 1
            if self.PauseFlag:
                #Set Pause flag for ingest of new archive objects
                ESSDB.DB().action('ESSProc','UPD',('Pause','1'),('Name','SIPReceiver'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','1'),('Name','AIPCreator'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','1'),('Name','AIPChecksum'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','1'),('Name','AIPValidate'))
            else:
                #Remove Pause flag for ingest of new archive objects
                ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','SIPReceiver'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPCreator'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPChecksum'))
                ESSDB.DB().action('ESSProc','UPD',('Pause','0'),('Name','AIPValidate'))
            db.close_old_connections()
            self.mLock.release()
            time.sleep(int(self.Time))
        self.RunFlag=0
        self.mDieFlag=0

    ################################################
    def __init__(self,ProcName):
            self.RunFlag=1
            self.mDieFlag=0                 #Flag to let thread die
            self.mQueue=[]
            self.mLock=thread.allocate_lock()
            thread.start_new_thread(WorkingThread.ThreadMain,(self,ProcName))

    #################################################
    def Die(self):
            self.mDieFlag=1
            while self.mDieFlag==1: pass

    ##################################################
    def AddItem(self,item):
            self.mLock.acquire()
            self.mQueue.append(item)
            self.mLock.release()
            return 1

#######################################################################################################
# Dep:
# Table: ESSProc with Name: AIPWriter, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Table: ESSConfig with Name: PolicyTable Value: archpolicy
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPWriter'
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
    ###########################
    # SocketHandler
    essSocketHandler = ESSlogging.ESSSocketHandler('localhost',60100)
    ##########################
    # Add handlers to default logger
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    esslogger = logging.getLogger('')
    esslogger.setLevel(0)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        esslogger.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            break
        time.sleep(5)
    logger.info('test3: ' + str(x.RunFlag))
    del x

# ./AIPWriter.py
