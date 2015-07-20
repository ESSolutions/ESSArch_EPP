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
import os, thread, multiprocessing, datetime, time, logging, sys, shutil, stat, ESSDB, ESSMSSQL, ESSPGM, operator,subprocess, ESSlogging, pytz
from django.utils import timezone

from essarch.models import storage, storageMedium, ArchiveObject, robotQueue, robotdrives
#from essarch.libs import flush_transaction
from django import db

class Functions:
    tz = timezone.get_default_timezone()
    "Lists IOqueue for write IOs and write them to tape"
    ###############################################
    def WriteTapeProc(self,select_t_prefix,ActiveTapeIOs,ProcName):
        self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]

        self.writeworklist = ESSDB.DB().action('IOqueue','GET',('ObjectIdentifierValue','cmd','cmdprio','work_uuid','sm_list',
                                               'ObjectPath','date_created','Status','WriteSize'),
                                               ('cmd','10','and','Status','2','and','t_prefix',select_t_prefix))
        #sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location]
        #print 'self.writeworklist:',self.writeworklist
        self.numwriteobjects = len(self.writeworklist)
        for self.item in self.writeworklist:
            db.close_old_connections()
            self.ObjectIdentifierValue = self.item[0]
            ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue=self.ObjectIdentifierValue)
            self.cmd = self.item[1]
            self.cmdprio = self.item[2]
            self.uuid = self.item[3]
            self.sm_list = eval(self.item[4])
            self.t_type = self.sm_list[0]
            self.t_format = self.sm_list[1]
            self.t_block = self.sm_list[2]
            self.sm_maxCapacity = self.sm_list[3]
            self.t_prefix = self.sm_list[6]
            self.t_location = self.sm_list[7]
            self.ObjectPath = self.item[5]
            self.date_created = self.item[6]
            self.Status = self.item[7]
            self.WriteSize = self.item[8]
            self.t_id = ''
            logger.debug('self.item for prefix: ' + str(self.t_prefix) + ' , ' + str(self.item))
            logger.info('Start Tape Write Process object: %s, target: %s, IOuuid: %s', self.ObjectIdentifierValue,self.t_prefix,self.uuid)
            ESSDB.DB().action('IOqueue','UPD',('Status','5'),('work_uuid',self.uuid))

            ########################################################
            # Check access to self.ObjectPath and verify self.WriteSize
            ########################################################
            self.PMetaObjectPath = self.ObjectPath[:-4] + '_Package_METS.xml'
            # AIC fix - start
            status_code, info_list, self.AIC_UUID = ESSPGM.DB().GetAIC(self.ObjectIdentifierValue)
            if status_code > 0:
                logging.warning('Problem to get AIC info for ObjectUUID: %s, code: %s, info: %s' % (self.ObjectIdentifierValue,status_code,str(info_list)))
            else:
                logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
            self.AICObjectDIR,AICObjectFILE = os.path.split(self.ObjectPath)

            self.AICmets_objpath = os.path.join(self.AICObjectDIR,self.AIC_UUID + '_AIC_METS.xml')
            if not os.path.exists(self.AICmets_objpath):
                self.AICmets_objpath = None
            # AIC fix - end
            # Check self.ObjectPath
            self.Object_res = Functions().CheckFileSize(self.ObjectPath)
            if self.Object_res[1] == 0:
                self.ObjectSize = self.Object_res[0]
            else:
                logger.error('Problem to access object: ' + self.ObjectPath + ', work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','110'),('work_uuid',self.uuid))
                continue
                #sys.exit(110)
            # Check self.PMetaObjectPath
            self.MetaObject_res = Functions().CheckFileSize(self.PMetaObjectPath)
            if self.MetaObject_res[1] == 0:
                self.MetaObjectSize = self.MetaObject_res[0]
            else:
                logger.error('Problem to access metaobject: ' + self.PMetaObjectPath + ', work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','111'),('work_uuid',self.uuid))
                continue
                #sys.exit(111)
            # Check WriteSize
            if self.WriteSize:
                if not int(self.WriteSize) == int(self.ObjectSize) + int(self.MetaObjectSize):
                    logger.error('Problem defined WriteSize does not match actual filesizes for object: ' + self.ObjectPath + ', work_uuid: ' + str(self.uuid))
                    logger.error('self.WriteSize: ' + str(self.WriteSize))
                    logger.error('self.ObjectSize: ' + str(self.ObjectSize))
                    logger.error('self.MetaObjectSize: ' + str(self.MetaObjectSize))
                    ESSDB.DB().action('IOqueue','UPD',('Status','112'),('work_uuid',self.uuid))
                    continue
                    #sys.exit(112)
            else:
                self.WriteSize = int(self.ObjectSize) + int(self.MetaObjectSize)
                logger.info('WriteSize not defined, setting write size for object: ' + self.ObjectIdentifierValue + ' WriteSize: ' + str(self.WriteSize))

            ########################################################
            # Mount write tape
            ########################################################
            self.Mount_exitcode, self.t_id, self.tapedev, self.t_pos = ESSPGM.Robot().MountWritePos2(t_type=self.t_type, t_block=self.t_block, t_format=self.t_format, t_prefix=self.t_prefix, t_location=self.t_location, work_uuid=self.uuid)
            if self.Mount_exitcode==0: 
                logger.info('Succedd to mount write tape id: ' + self.t_id + ' dev: ' + self.tapedev + ' pos: ' + str(self.t_pos))
            elif self.Mount_exitcode==1:
                logger.error('Problem to mount tapes, Stopping ' + ProcName + ', work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','102'),('work_uuid',self.uuid))
                sys.exit(102)
            elif self.Mount_exitcode==2:
                logger.error('No empty tapes are available, flag ' + ProcName + ' to stop' + ', work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','103'),('work_uuid',self.uuid))
                sys.exit(103)
            elif self.Mount_exitcode==3:
                logger.error('Failed to verify tape after full write, flag ' + ProcName + ' to stop, work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','104'),('work_uuid',self.uuid))
                sys.exit(104)

            ########################################################
            # Verify tape position and check write/tape size
            ########################################################
            #flush_transaction()
            storageMedium_obj = storageMedium.objects.get(storageMediumID=self.t_id)
            self.new_t_size = storageMedium_obj.storageMediumUsedCapacity + int(self.WriteSize)
            #self.new_t_size=int(ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumUsedCapacity',),('storageMediumID',self.t_id))[0][0]) + int(self.WriteSize)
            if self.new_t_size > self.sm_maxCapacity and self.sm_maxCapacity > 0:
                logger.info('Tape id: %s has reached maximum configured tape size: %s bytes. IOuuid: %s',self.t_id,str(self.sm_maxCapacity),str(self.uuid))
                ###################################################
                # Release lock for tapedrive
                res, errno = Functions().ReleaseTapeLock(self.uuid)
                if errno == 0:
                    logger.info(res)
                else:
                    logger.error(res)                                        
                ###################################################
                # Verify tapeid and full mark and mount a new tape
                ###################################################
                self.Mount_exitcode, self.t_id, self.tapedev, self.t_pos = ESSPGM.Robot().MountWritePos2(t_type=self.t_type, t_block=self.t_block, t_format=self.t_format, t_prefix=self.t_prefix, t_location=self.t_location, full_t_id=self.t_id, work_uuid=self.uuid)
                if self.Mount_exitcode==0:
                    logger.info('Succedd to mount write tape id: ' + self.t_id + ' dev: ' + self.tapedev + ' pos: ' + str(self.t_pos))
                    #flush_transaction()
                    storageMedium_obj = storageMedium.objects.get(storageMediumID=self.t_id)
                    self.new_t_size = storageMedium_obj.storageMediumUsedCapacity + int(self.WriteSize)
                    #self.new_t_size=int(ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumUsedCapacity',),('storageMediumID',self.t_id))[0][0]) + int(self.WriteSize)
                elif self.Mount_exitcode==1:
                    logger.error('Problem to mount tapes, Stopping ' + ProcName + ', work_uuid: ' + str(self.uuid))
                    ESSDB.DB().action('IOqueue','UPD',('Status','102'),('work_uuid',self.uuid))
                    sys.exit(102)
                elif self.Mount_exitcode==2:
                    logger.error('No empty tapes are avilable, flag ' + ProcName + ' to stop' + ', work_uuid: ' + str(self.uuid))
                    ESSDB.DB().action('IOqueue','UPD',('Status','103'),('work_uuid',self.uuid))
                    sys.exit(103)
                elif self.Mount_exitcode==3:
                    logger.error('Failed to verify tape after full write, flag ' + ProcName + ' to stop, work_uuid: ' + str(self.uuid))
                    ESSDB.DB().action('IOqueue','UPD',('Status','104'),('work_uuid',self.uuid))
                    sys.exit(104)
            logger.info('New tape size for t_id: ' + self.t_id + ' is: '+str(self.new_t_size))
            self.current_t_pos,errno,why = ESSPGM.Robot().MTFilenum(self.tapedev)
            if errno:
                logger.error('Problem to get current tape position, why: ' + why + ', flag ' + ProcName + ' to stop' + ', work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','106'),('work_uuid',self.uuid))
                sys.exit(106)
            logger.info('Current t_pos: ' + str(self.current_t_pos) + ' for t_id: '+str(self.t_id))
            latest_storage_qs = storage.objects.filter(storageMediumUUID__storageMediumID=self.t_id).order_by('-id')[:1]
            if latest_storage_qs.exists():
                self.db_t_pos = int(latest_storage_qs[0].contentLocationValue) + 1
            #self.db_t_pos = ESSDB.DB().action(self.StorageTable,'GETlast',('id','contentLocationValue'),('storageMediumID','=','"'+self.t_id+'"'))
            #if len(self.db_t_pos):
            #    self.t_pos = int(self.db_t_pos[0][1]) + 1
            else:
                self.t_pos = 1
            logger.info('New DB t_pos: ' + str(self.t_pos) + ' for t_id: '+str(self.t_id))
            if self.current_t_pos == self.t_pos:
                ########################################################
                # Write AIP package to tape
                ########################################################
                self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                #self.Write_cmdres = Functions().WritePackage(tapedev,t_block,ObjectIdentifierValue,ObjectPath,PMetaObjectPath)
                self.PMetaObjectPath = self.ObjectPath[:-4] + '_Package_METS.xml'
                # AIC fix - start
                status_code, info_list, self.AIC_UUID = ESSPGM.DB().GetAIC(self.ObjectIdentifierValue)
                if status_code > 0:
                    logging.warning('Problem to get AIC info for ObjectUUID: %s, code: %s, info: %s' % (self.ObjectIdentifierValue,status_code,str(info_list)))
                else:
                    logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
                self.AICObjectDIR,AICObjectFILE = os.path.split(self.ObjectPath)

                self.AICmets_objpath = os.path.join(self.AICObjectDIR,self.AIC_UUID + '_AIC_METS.xml')
                if not os.path.exists(self.AICmets_objpath):
                    self.AICmets_objpath = None
                # AIC fix - end
                self.Write_cmdres = Functions().WritePackage2(self.tapedev,self.t_block,self.ObjectIdentifierValue,self.ObjectPath,self.PMetaObjectPath,self.AICmets_objpath)
                logger.info('WritePackage cmdres: ' + str(self.Write_cmdres) + ' for t_id: '+str(self.t_id))
                if self.Write_cmdres[0]==0:
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    ##########################
                    # Insert StorageTable
                    storage_obj = storage()
                    storage_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                    storage_obj.contentLocationType = 300
                    storage_obj.contentLocationValue = self.t_pos
                    storage_obj.storageMediumID = self.t_id
                    storage_obj.storageMediumUUID = storageMedium_obj
                    storage_obj.ObjectUUID = ArchiveObject_obj
                    #storage_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                    storage_obj.LocalDBdatetime = self.timestamp_utc
                    storage_obj.save()
                    #res,errno,why = ESSDB.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
                    #                                                           'contentLocationType','300',
                    #                                                           'contentLocationValue',self.t_pos,
                    #                                                           'storageMediumID',self.t_id,
                    #                                                           'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
                    #if errno: logger.error('Failed to insert to Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    #if errno == 0 and ExtDBupdate:
                    if ExtDBupdate:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
                                                                                                  'contentLocationType','300',
                                                                                                  'contentLocationValue',self.t_pos,
                                                                                                  'storageMediumID',self.t_id))
                        if ext_errno: logger.error('Failed to insert to External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                        else:
                            #storage_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                            storage_obj.ExtDBdatetime = self.timestamp_utc
                            storage_obj.save(update_fields=['ExtDBdatetime'])
                            #res,errno,why = ESSDB.DB().action(self.StorageTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                            #                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND',
                            #                                                           'contentLocationType','300','AND',
                            #                                                           'contentLocationValue',self.t_pos,'AND',
                            #                                                           'storageMediumID',self.t_id))
                            #if errno: logger.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    ##########################
                    # Update StorageMediumTable
                    storageMedium_obj.storageMediumUsedCapacity = self.new_t_size
                    #storageMedium_obj.storageMediumDate = self.timestamp_utc.replace(tzinfo=None)
                    storageMedium_obj.storageMediumDate = self.timestamp_utc
                    storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                    #storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                    storageMedium_obj.LocalDBdatetime = self.timestamp_utc
                    storageMedium_obj.save(update_fields=['storageMediumUsedCapacity','storageMediumDate','linkingAgentIdentifierValue','LocalDBdatetime'])
                    #res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_t_size,
                    #                                                                 'storageMediumDate',self.timestamp_utc.replace(tzinfo=None),
                    #                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                    #                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                    #                                                                ('storageMediumID',self.t_id))
                    #if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                    #if errno == 0 and ExtDBupdate:
                    if ExtDBupdate:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_t_size,
                                                                                                        'storageMediumDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                        'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                       ('storageMediumID',self.t_id))
                        if ext_errno: logger.error('Failed to update External DB: ' + str(self.t_id) + ' error: ' + str(ext_why))
                        else:
                            #storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                            storageMedium_obj.ExtDBdatetime = self.timestamp_utc
                            storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                            #res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                            #if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                    if storage.objects.filter(ObjectUUID__ObjectIdentifierValue=self.ObjectIdentifierValue, storageMediumUUID__storageMediumID=self.t_id).exists():
                    #if ESSDB.DB().action(self.StorageTable,'GET',('id',),('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND','storageMediumID',self.t_id)):                        
                        self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        self.writetime = self.stopTime-self.startTime
                        self.writesize = int(self.WriteSize)/1048576
                        if self.writetime.seconds < 1: self.writetime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                        self.MBperSEC = int(self.writesize)/int(self.writetime.seconds)
                        logger.info('Succedd to write IOuuid: %s for Object: %s to tape (%s MB/Sec)',str(self.uuid), self.ObjectIdentifierValue, str(self.MBperSEC))
                        ESSDB.DB().action('IOqueue','UPD',('Status','20'),('work_uuid',self.uuid))
                        ###################################################
                        # Release lock for tapedrive
                        res, errno = Functions().ReleaseTapeLock(self.uuid)
                        if errno == 0:
                            logger.info(res)
                        else:
                            logger.error(res)                                        

                #elif self.cmdres[0]==28: # 28=full tape with python tar
                elif self.Write_cmdres[0]==2: # 2=full tape with SUSE tar
                    #Tape is full
                    #Hardclose writeobject (Only used with "FunctionThread().WritePackage")
                    #self.cmdres = writer().hardclose(self.writeobject)
                    ###################################################
                    # Release lock for tapedrive
                    res, errno = Functions().ReleaseTapeLock(self.uuid)
                    if errno == 0:
                        logger.info(res)
                    else:
                        logger.error(res)                                        
                    ########################################################
                    # Tape is full quickverify tape and then mount a new write tape
                    ########################################################
                    self.Mount_exitcode, self.t_id, self.tapedev, self.t_pos = ESSPGM.Robot().MountWritePos2(t_type=self.t_type, t_block=self.t_block, t_format=self.t_format, t_prefix=self.t_prefix, t_location=self.t_location, full_t_id=self.t_id, work_uuid=self.uuid)
                    if self.Mount_exitcode==0:
                        logger.info('Succedd to mount write tape id: ' + self.t_id + ' dev: ' + self.tapedev + ' pos: ' + str(self.t_pos))
                        #flush_transaction()
                        storageMedium_obj = storageMedium.objects.get(storageMediumID=self.t_id)
                        self.new_t_size = storageMedium_obj.storageMediumUsedCapacity + int(self.WriteSize)
                        #self.new_t_size=int(ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumUsedCapacity',),('storageMediumID',self.t_id))[0][0]) + int(self.WriteSize)
                        logger.info('New tape size for t_id: ' + self.t_id + ' is: '+str(self.new_t_size))
                        self.current_t_pos,errno,why = ESSPGM.Robot().MTFilenum(self.tapedev)
                        if errno:
                            logger.error('Problem to get current tape position, why: ' + why + ', flag ' + ProcName + ' to stop' + ', work_uuid: ' + str(self.uuid))
                            ESSDB.DB().action('IOqueue','UPD',('Status','106'),('work_uuid',self.uuid))
                            sys.exit(106)
                        logger.info('Current t_pos: ' + str(self.current_t_pos) + ' for t_id: '+str(self.t_id))
                        latest_storage_qs = storage.objects.filter(storageMediumUUID__storageMediumID=self.t_id).order_by('-id')[:1]
                        if latest_storage_qs.exists():
                            self.db_t_pos = int(latest_storage_qs[0].contentLocationValue) + 1
                        #self.db_t_pos = ESSDB.DB().action(self.StorageTable,'GETlast',('id','contentLocationValue'),('storageMediumID','=','"'+self.t_id+'"'))
                        #if len(self.db_t_pos):
                        #    self.t_pos = int(self.db_t_pos[0][1]) + 1
                        else:
                            self.t_pos = 1
                        logger.info('New DB t_pos: ' + str(self.t_pos) + ' for t_id: '+str(self.t_id))
                        if self.current_t_pos == self.t_pos:
                            ########################################################
                            # Write AIP package to tape after tapechange
                            ########################################################
                            #self.Write_cmdres = Functions().WritePackage(self.tapedev,self.t_block,self.ObjectIdentifierValue,self.ObjectPath,self.PMetaObjectPath)
                            self.Write_cmdres = Functions().WritePackage2(self.tapedev,self.t_block,self.ObjectIdentifierValue,self.ObjectPath,self.PMetaObjectPath,self.AICmets_objpath)
                            if self.Write_cmdres[0]==0:
                                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                ##########################
                                # Insert StorageTable
                                storage_obj = storage()
                                storage_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                                storage_obj.contentLocationType = 300
                                storage_obj.contentLocationValue = self.t_pos
                                storage_obj.storageMediumID = self.t_id
                                storage_obj.storageMediumUUID = storageMedium_obj
                                storage_obj.ObjectUUID = ArchiveObject_obj
                                #storage_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                storage_obj.LocalDBdatetime = self.timestamp_utc
                                storage_obj.save()
                                #res,errno,why = ESSDB.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
                                #                                                           'contentLocationType','300',
                                #                                                           'contentLocationValue',self.t_pos,
                                #                                                           'storageMediumID',self.t_id,
                                #                                                           'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
                                #if errno: logger.error('Failed to insert to Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                #if errno == 0 and ExtDBupdate:
                                if ExtDBupdate:
                                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
                                                                                                              'contentLocationType','300',
                                                                                                              'contentLocationValue',self.t_pos,
                                                                                                              'storageMediumID',self.t_id))
                                    if ext_errno: logger.error('Failed to insert to External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                                    else:
                                        #storage_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                        storage_obj.ExtDBdatetime = self.timestamp_utc
                                        storage_obj.save(update_fields=['ExtDBdatetime'])
                                        #res,errno,why = ESSDB.DB().action(self.StorageTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                        #                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND',
                                        #                                                           'contentLocationType','300','AND',
                                        #                                                           'contentLocationValue',self.t_pos,'AND',
                                        #                                                           'storageMediumID',self.t_id))
                                        #if errno: logger.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                                ##########################
                                # Update StorageMediumTable
                                storageMedium_obj.storageMediumUsedCapacity = self.new_t_size
                                #storageMedium_obj.storageMediumDate = self.timestamp_utc.replace(tzinfo=None)
                                storageMedium_obj.storageMediumDate = self.timestamp_utc
                                storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                                #storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                storageMedium_obj.LocalDBdatetime = self.timestamp_utc
                                storageMedium_obj.save(update_fields=['storageMediumUsedCapacity','storageMediumDate','linkingAgentIdentifierValue','LocalDBdatetime'])
                                #res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_t_size,
                                #                                                                 'storageMediumDate',self.timestamp_utc.replace(tzinfo=None),
                                #                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                                #                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                #                                                                ('storageMediumID',self.t_id))
                                #if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                                #if errno == 0 and ExtDBupdate:
                                if ExtDBupdate:
                                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_t_size,
                                                                                                                    'storageMediumDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                                   ('storageMediumID',self.t_id))
                                    if ext_errno: logger.error('Failed to update External DB: ' + str(self.t_id) + ' error: ' + str(ext_why))
                                    else:
                                        #storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                        storageMedium_obj.ExtDBdatetime = self.timestamp_utc
                                        storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                                        #res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                                        #if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))

                                if storage.objects.filter(ObjectUUID__ObjectIdentifierValue=self.ObjectIdentifierValue, storageMediumUUID__storageMediumID=self.t_id).exists():
                                #if ESSDB.DB().action(self.StorageTable,'GET',('id',),('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND','storageMediumID',self.t_id)):
                                    self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                                    self.writetime = self.stopTime-self.startTime
                                    self.writesize = int(self.WriteSize)/1048576
                                    if self.writetime.seconds < 1: self.writetime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                                    self.MBperSEC = int(self.writesize)/int(self.writetime.seconds)
                                    logger.info('Succedd to write IOuuid: %s for Object: %s to tape (%s MB/Sec)',str(self.uuid), self.ObjectIdentifierValue, str(self.MBperSEC))
                                    ESSDB.DB().action('IOqueue','UPD',('Status','20'),('work_uuid',self.uuid))
                                    ###################################################
                                    # Release lock for tapedrive
                                    res, errno = Functions().ReleaseTapeLock(self.uuid)
                                    if errno == 0:
                                        logger.info(res)
                                    else:
                                        logger.error(res)                                        
                            else:
                                logger.error('Problem to write a copy of '+self.ObjectIdentifierValue+' to tape ' + self.t_id + ' , work_uuid: ' + str(self.uuid))
                                ESSDB.DB().action('IOqueue','UPD',('Status','101'),('work_uuid',self.uuid))
                                sys.exit(101)
                        else:
                            logger.error('Current-tape position and DB-tape position missmatch for '+self.ObjectIdentifierValue+' to tape ' + self.t_id + ' , work_uuid: ' + str(self.uuid))
                            ESSDB.DB().action('IOqueue','UPD',('Status','105'),('work_uuid',self.uuid))
                            sys.exit(105)
                    elif self.Mount_exitcode==1:
                        logger.error('Problem to mount new tape, flag ' + ProcName + ' to stop, work_uuid: ' + str(self.uuid))
                        ESSDB.DB().action('IOqueue','UPD',('Status','102'),('work_uuid',self.uuid))
                        sys.exit(102)
                    elif self.Mount_exitcode==2:
                        logger.error('No empty tapes are avilable, flag ' + ProcName + ' to stop, work_uuid: ' + str(self.uuid))
                        ESSDB.DB().action('IOqueue','UPD',('Status','103'),('work_uuid',self.uuid))
                        sys.exit(103)
                    elif self.Mount_exitcode==3:
                        logger.error('Failed to verify tape after full write, flag ' + ProcName + ' to stop, work_uuid: ' + str(self.uuid))
                        ESSDB.DB().action('IOqueue','UPD',('Status','104'),('work_uuid',self.uuid))
                        sys.exit(104)
                else:
                    logger.error('Problem to write a copy of '+self.ObjectIdentifierValue+' to tape ' + self.t_id  + ' , work_uuid: ' + str(self.uuid))
                    ESSDB.DB().action('IOqueue','UPD',('Status','101'),('work_uuid',self.uuid))
                    sys.exit(101)
            else:
                logger.error('Current-tape position and DB-tape position missmatch for '+self.ObjectIdentifierValue+' to tape ' + self.t_id + ' , work_uuid: ' + str(self.uuid))
                ESSDB.DB().action('IOqueue','UPD',('Status','105'),('work_uuid',self.uuid))
                sys.exit(105)
        ActiveTapeIOs.remove(select_t_prefix)

    ###############################################
    def WritePackage(self,tapedev,t_block,ObjectIdentifierValue,ObjectPath,PMetaObjectPath):
        # Open writeobject
        self.writeobject = ESSPGM.writer().open(tapedev,'w|',t_block)
        if self.writeobject[0]==0:
            # Write ObjectPath to writeobject
            self.cmdres = ESSPGM.writer().addfile(self.writeobject[2],ObjectPath,ObjectIdentifierValue+'.tar')
            if self.cmdres[0]==0:
                # Write PMetaObjectPath to writeobject
                self.cmdres = ESSPGM.writer().addfile(self.writeobject[2],PMetaObjectPath,ObjectIdentifierValue+'.RES')
                if self.cmdres[0]==0:
                    # Close writeobject
                    self.cmdres = ESSPGM.writer().close(self.writeobject[2])
            return self.cmdres[0],self.cmdres[1]
        else:
            return self.writeobject[0],self.writeobject[1]

    ###############################################
    def WritePackage2(self,tapedev,t_block,ObjectIdentifierValue,ObjectPath,PMetaObjectPath,AICmets_objpath):
        self.ObjectDIR,ObjectFILE = os.path.split(ObjectPath)
        self.MetaObjectDIR,MetaObjectFILE = os.path.split(PMetaObjectPath)
        if AICmets_objpath is not None:
            self.AICObjectDIR,AICObjectFILE = os.path.split(AICmets_objpath)
        else:
            self.AICObjectDIR = None
            AICObjectFILE = None
        # Open writeobject
        self.writeresult = ESSPGM.writer().subtar(tapedev,t_block,self.ObjectDIR,ObjectFILE,MetaObjectFILE,AICObjectFILE)
        return self.writeresult[0],self.writeresult[1],self.writeresult[2]

    "Readtapeproc"
    ##############################################
    def ReadTapeProc(self,t_id,ActiveTapeIOs,ProcName):
        self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
        #self.RobotReqTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotReqTable'))[0][0]
        self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]

        self.readworklist = ESSDB.DB().action('IOqueue','GET',('ObjectIdentifierValue','cmd','cmdprio','work_uuid','storageMediumID','sm_list',
                                                               'ObjectPath','date_created','Status','ObjectMessageDigest'),
                                                              ('cmd','20','and','Status','2','and','storageMediumID',t_id))

        #sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location,self.contentLocationValue]

        self.numreadobjects = len(self.readworklist)
        for self.item in self.readworklist:
            #if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0]=='0':
            #    logger.info('Stopping ' + ProcName)
            #    ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0'),('Name',ProcName))
            #    break
            self.ObjectIdentifierValue = self.item[0]
            self.cmd = self.item[1]
            self.cmdprio = self.item[2]
            self.uuid = self.item[3]
            self.t_id = self.item[4]
            self.sm_list = eval(self.item[5])
            if not self.sm_list[1] is None: 
                try:
                    self.sm_format = int(self.sm_list[1])
                except ValueError:
                    self.sm_format = None
            else:
                self.sm_format = None
            self.t_num = self.sm_list[8]
            self.t_block = self.sm_list[2]
            self.ObjectPath = self.item[6]
            self.date_created = self.item[7]
            self.Status = self.item[8]
            self.p_sum = self.item[9]
            self.MessageDigestAlgorithm = ESSDB.DB().action(self.IngestTable,'GET',('ObjectMessageDigestAlgorithm',),('ObjectIdentifierValue',self.ObjectIdentifierValue))[0][0]
            logger.debug('self.item for tapeid: ' + str(t_id) + ' , ' + str(self.item))
            logger.info('Start Tape Read Process object: %s, target: %s, IOuuid: %s', self.ObjectIdentifierValue,self.t_id,self.uuid)
            ESSDB.DB().action('IOqueue','UPD',('Status','5'),('work_uuid',self.uuid))

            #########################################
            # Check if tape is mounted
            #########################################
            self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id','drive_lock','drive_dev'),('t_id',self.t_id,'AND','status','Mounted'))
            if self.robotdrive:
                while 1:
                    self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id','drive_lock','drive_dev'),('t_id',self.t_id,'AND','status','Mounted'))
                    self.drive_id = self.robotdrive[0][0]
                    self.current_lock = self.robotdrive[0][1]
                    self.tapedev = self.robotdrive[0][2]
                    ##########################################
                    #Tape is mounted, check if locked
                    if len(self.current_lock) > 0:
                        ########################################
                        # Tape is locked, check if req work_uuid = lock
                        if self.current_lock == self.uuid:
                            ########################################
                            # Tape is already locked with req work_uuid
                            logger.info('Already Mounted: ' + str(self.t_id) + ' and locked by req work_uuid: ' + str(self.uuid))
                            break
                        else:
                            ########################################
                            # Tape is locked with another work_uuid
                            logger.info('Tape: ' + str(self.t_id) + ' is busy and locked by: ' + str(self.current_lock) + ' and not req work_uuid: ' + str(self.uuid))
                    else:
                        ########################################
                        # Tape is not locked, lock the drive with req work_uuid
                        ESSDB.DB().action(self.RobotDrivesTable,'UPD',('drive_lock',self.uuid),('drive_id',self.drive_id))
                        logger.info('Tape: ' + str(self.t_id) + ' is available set lock to req work_uuid: ' + str(self.uuid))
                        break
                    time.sleep(5)
            else:
                #Tape is not mounted, mounting tape
                logger.info('Start to mount: ' + str(self.t_id))
                robotQueue_obj = robotQueue()
                robotQueue_obj.ReqUUID = self.uuid
                robotQueue_obj.ReqType = 50 # Mount
                robotQueue_obj.ReqPurpose = 'IOEngine - ReadTapeProc'
                robotQueue_obj.Status = 0 # Pending
                robotQueue_obj.MediumID = self.t_id
                robotQueue_obj.save()
                #ESSDB.DB().action(self.RobotReqTable,'INS',('job_prio','1','status','Pending','req_type','Mount','t_id',self.t_id,'work_uuid',self.uuid))
                while 1:
                    self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_dev',),('t_id',self.t_id,'AND','status','Mounted','AND','drive_lock',self.uuid))
                    if self.robotdrive:
                        logger.info('Mount succeeded: ' + str(self.t_id))
                        self.tapedev = self.robotdrive[0][0]
                        break
                    else:
                        #self.req_status = ESSDB.DB().action(self.RobotReqTable,'GET',('status',),('work_uuid',self.uuid))
                        self.req_status = robotQueue.objects.filter( ReqUUID=self.uuid ).all()
                        if self.req_status:
                            #if self.req_status[0][0] == 'Fail':
                            if self.req_status[0].Status == 100:
                                self.tapedev = None
                                break
                        logger.info('Wait for mounting of: ' + str(self.t_id))
                    time.sleep(2)

            if self.tapedev:
                self.extractdir, self.ObjectFilename = os.path.split(self.ObjectPath)
                self.PMetaObjectFilename = self.ObjectFilename[:-4] + '_Package_METS.xml'
                # AIC fix - start
                status_code, info_list, self.AIC_UUID = ESSPGM.DB().GetAIC(self.ObjectIdentifierValue)
                if status_code > 0:
                    logging.warning('Problem to get AIC info for ObjectUUID: %s, code: %s, info: %s' % (self.ObjectIdentifierValue,status_code,str(info_list)))
                else:
                    logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
                self.AICmets_objFilename = self.AIC_UUID + '_AIC_METS.xml'
                # AIC fix - end
                self.tmpextractdir = os.path.join(self.extractdir,'.tmpextract')
                if not os.path.exists(self.tmpextractdir):
                    os.mkdir(self.tmpextractdir)
                ###########################################
                # Position tape
                ###########################################
                if ESSPGM.Robot().MTPosition(self.tapedev, self.t_num) == 'OK':
                    ######################################################
                    # Tar extract tape
                    ######################################################
                    logger.info('Start to extract tapefile: ' + str(self.t_num) + ' ' + str(self.tapedev)  + ' ' + str(self.ObjectFilename))
                    if self.sm_format in range(100,102):
                        self.cmd = subprocess.Popen(["tar","-b",str(self.t_block),"-C",str(self.tmpextractdir),"-x","-f",str(self.tapedev),str(self.ObjectFilename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    elif self.sm_format == 102:
                        self.cmd = subprocess.Popen(["tar","-b",str(self.t_block),"-C",str(self.tmpextractdir),"-x","-f",str(self.tapedev),str(self.ObjectFilename),str(self.PMetaObjectFilename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    elif self.sm_format == 103:
                        self.cmd = subprocess.Popen(["tar","-b",str(self.t_block),"-C",str(self.tmpextractdir),"-x","-f",str(self.tapedev),str(self.ObjectFilename),str(self.PMetaObjectFilename),str(self.AICmets_objFilename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    self.tarout = self.cmd.communicate()
                    if self.cmd.returncode == 0:
                        self.event_info = 'Success to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s' % (self.ObjectIdentifierValue, t_id, self.tmpextractdir,  self.uuid)
                        logger.info(self.event_info)
                        ESSPGM.Events().create('1105','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                        #############################################
                        # Checksum Check
                        #############################################
                        self.tp_sum,errno,why = ESSPGM.Check().checksum(os.path.join(self.tmpextractdir,self.ObjectFilename),self.MessageDigestAlgorithm) # Checksum
                        if errno:
                            self.event_info = 'Failed to get checksum for: %s, Error: %s' % (os.path.join(self.tmpextractdir,self.ObjectFilename),str(why))
                            logger.error(self.event_info)
                            ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        else:
                            self.event_info = 'Success to get checksum for: %s, Checksum: %s' % (os.path.join(self.tmpextractdir,self.ObjectFilename),self.tp_sum)
                            logger.info(self.event_info)
                            ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                        if str(self.tp_sum) == str(self.p_sum):
                            self.event_info = 'Success to verify checksum for Object %s in tmpDIP: %s, IOuuid: %s' % (self.ObjectIdentifierValue, self.tmpextractdir, self.uuid)
                            logger.info(self.event_info)
                            ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                            #############################
                            # Move files to req path
                            #############################
                            shutil.move(os.path.join(self.tmpextractdir,self.ObjectFilename),self.ObjectPath) 
                            if not self.sm_format in range(100,102):
                                shutil.move(os.path.join(self.tmpextractdir,self.PMetaObjectFilename),os.path.join(self.extractdir,self.PMetaObjectFilename)) 
                                if os.path.exists(os.path.join(self.tmpextractdir,self.AICmets_objFilename)):
                                    shutil.move(os.path.join(self.tmpextractdir,self.AICmets_objFilename),os.path.join(self.extractdir,self.AICmets_objFilename)) 
                            logger.info('Succedd to read IOuuid: %s for Object: %s from tape (* MB/Sec)',str(self.uuid), self.ObjectIdentifierValue)
                            ESSDB.DB().action('IOqueue','UPD',('Status','20'),('work_uuid',self.uuid))
                            ###################################################
                            # Release lock for tapedrive
                            res, errno = Functions().ReleaseTapeLock(self.uuid)
                            if errno == 0:
                                logger.info(res)
                            else:
                                logger.error(res)
                        else:
                            ESSDB.DB().action('IOqueue','UPD',('Status','100'),('work_uuid',self.uuid))
                            self.event_info = 'Checksum verify mismatch for Object %s in tmpDIP: %s, IOuuid: %s, tape_checksum: %s, meta_checksum: %s' % (self.ObjectIdentifierValue, self.tmpextractdir, self.uuid, self.tp_sum, self.p_sum)
                            logger.error(self.event_info)
                            ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            ###################################################
                            # Release lock for tapedrive
                            res, errno = Functions().ReleaseTapeLock(self.uuid)
                            if errno == 0:
                                logger.info(res)
                            else:
                                logger.error(res)
                    else:
                        ESSDB.DB().action('IOqueue','UPD',('Status','100'),('work_uuid',self.uuid))
                        self.event_info = 'Problem to read tape for Object %s from SM: %s, IOuuid: %s, Error: %s' % (self.ObjectIdentifierValue, t_id, self.uuid, str(self.tarout))
                        logger.error(self.event_info)
                        ESSPGM.Events().create('1105','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        ###################################################
                        # Release lock for tapedrive
                        res, errno = Functions().ReleaseTapeLock(self.uuid)
                        if errno == 0:
                            logger.info(res)
                        else:
                            logger.error(res)
                else:
                    ESSDB.DB().action('IOqueue','UPD',('Status','100'),('work_uuid',self.uuid))
                    self.event_info = 'Problem to position tape for Object %s from SM: %s, IOuuid: %s, Error: %s' % (self.ObjectIdentifierValue, t_id, self.uuid, '')
                    logger.error(self.event_info)
                    ESSPGM.Events().create('1105','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    ###################################################
                    # Release lock for tapedrive
                    res, errno = Functions().ReleaseTapeLock(self.uuid)
                    if errno == 0:
                        logger.info(res)
                    else:
                        logger.error(res)
            else:
                ESSDB.DB().action('IOqueue','UPD',('Status','100'),('work_uuid',self.uuid))
                self.event_info = 'Problem to access tapedevice for Object %s from SM: %s, IOuuid: %s, Error: %s' % (self.ObjectIdentifierValue, t_id, self.uuid, '')
                logger.error(self.event_info)
                ESSPGM.Events().create('1105','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                ###################################################
                # Release lock for tapedrive
                res, errno = Functions().ReleaseTapeLock(self.uuid)
                if errno == 0:
                    logger.info(res)
                else:
                    logger.error(res)
        ActiveTapeIOs.remove(t_id)

    "Write IOuuid to disk"
    ###############################################
    def WriteDiskProc(self,uuid,ObjectIdentifierValue,ObjectPath,WriteSize,sm_list):
        self.run = 1
        db.close_old_connections()
        self.process_name = multiprocessing.current_process().name
        self.process_pid = multiprocessing.current_process().pid
        self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        self.uuid = uuid
        self.ObjectIdentifierValue = ObjectIdentifierValue
        ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue=self.ObjectIdentifierValue)
        self.ObjectPath = ObjectPath
        self.WriteSize = WriteSize
        self.sm_type = sm_list[0]
        self.sm_format = sm_list[1]
        self.sm_blocksize = sm_list[2]
        self.sm_maxCapacity = sm_list[3]
        self.sm_minChunkSize = sm_list[4]
        self.sm_minContainerSize = sm_list[5]
        self.sm_target = sm_list[6]
        self.sm_location = sm_list[7]

        logger.debug('WriteDiskProc start with IOuuid: %s, Object: %s, ObjectPath: %s, WriteSize: %s, sm_list: %s, name: %s, pid: %s', self.uuid, self.ObjectIdentifierValue, self.ObjectPath, self.WriteSize, str(sm_list), self.process_name, self.process_pid)
        logger.info('Start Disk Write Process for object: %s, target: %s, IOuuid: %s', self.ObjectIdentifierValue,self.sm_target,self.uuid)
        ESSDB.DB().action('IOqueue','UPD',('Status','5'),('work_uuid',self.uuid))

        ########################################################
        # Check access to self.ObjectPath and verify self.WriteSize
        ########################################################
        self.PMetaObjectPath = self.ObjectPath[:-4] + '_Package_METS.xml'
        # AIC fix - start
        status_code, info_list, self.AIC_UUID = ESSPGM.DB().GetAIC(self.ObjectIdentifierValue)
        if status_code > 0:
            logging.warning('Problem to get AIC info for ObjectUUID: %s, code: %s, info: %s' % (self.ObjectIdentifierValue,status_code,str(info_list)))
        else:
            logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
        self.AICObjectDIR,AICObjectFILE = os.path.split(self.ObjectPath)

        self.AICmets_objpath = os.path.join(self.AICObjectDIR,self.AIC_UUID + '_AIC_METS.xml')
        if not os.path.exists(self.AICmets_objpath):
            self.AICmets_objpath = None
        # AIC fix - end
        # Check self.ObjectPath
        self.Object_res = Functions().CheckFileSize(self.ObjectPath)
        if self.Object_res[1] == 0:
            self.ObjectSize = self.Object_res[0]
        else:
            logger.error('Problem to access object: ' + self.ObjectPath + ', IOuuid: ' + str(self.uuid))
            ESSDB.DB().action('IOqueue','UPD',('Status','110'),('work_uuid',self.uuid))
            self.run = 0
            #sys.exit(110)
        # Check self.PMetaObjectPath
        self.MetaObject_res = Functions().CheckFileSize(self.PMetaObjectPath)
        if self.MetaObject_res[1] == 0:
            self.MetaObjectSize = self.MetaObject_res[0]
        else:
            logger.error('Problem to access metaobject: ' + self.PMetaObjectPath + ', IOuuid: ' + str(self.uuid))
            ESSDB.DB().action('IOqueue','UPD',('Status','111'),('work_uuid',self.uuid))
            self.run = 0
            #sys.exit(111)
        # Check WriteSize
        if self.WriteSize:
            if not int(self.WriteSize) == int(self.ObjectSize) + int(self.MetaObjectSize):
                logger.error('Problem defined WriteSize does not match actual filesizes for object: ' + self.ObjectPath + ', IOuuid: ' + str(self.uuid))
                logger.error('self.WriteSize: ' + str(self.WriteSize))
                logger.error('self.ObjectSize: ' + str(self.ObjectSize))
                logger.error('self.MetaObjectSize: ' + str(self.MetaObjectSize))
                ESSDB.DB().action('IOqueue','UPD',('Status','112'),('work_uuid',self.uuid))
                self.run = 0
                #sys.exit(112)
        else:
            self.WriteSize = int(self.ObjectSize) + int(self.MetaObjectSize)
            logger.info('WriteSize not defined, setting write size for object: ' + self.ObjectIdentifierValue + ' WriteSize: ' + str(self.WriteSize))
        # Check if StorageMediumID 'disk' exist, if exist get current target size.
        try:
            #flush_transaction()
            storageMedium_obj = storageMedium.objects.get(storageMediumID='disk')
        except storageMedium.DoesNotExist, why:
            logger.error('Problem to access DB_storageMediumID disk for IOuuid: ' + str(self.uuid))
            ESSDB.DB().action('IOqueue','UPD',('Status','113'),('work_uuid',self.uuid))
            self.run = 0
        else:
            self.new_target_size = storageMedium_obj.storageMediumUsedCapacity + int(self.WriteSize)     
#        self.db_storageMediumID = ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumUsedCapacity',),('storageMediumID','disk'))
#        if self.db_storageMediumID:
#            self.current_target_size = self.db_storageMediumID[0][0]
#            self.new_target_size=int(self.current_target_size) + int(self.WriteSize)
#        else:
#            logger.error('Problem to access DB_storageMediumID disk for IOuuid: ' + str(self.uuid))
#            ESSDB.DB().action('IOqueue','UPD',('Status','113'),('work_uuid',self.uuid))
#            self.run = 0

        # Check write access to target directory
        if not os.access(self.sm_target, 7): 
            logger.error('Problem to access target directory: ' + self.sm_target + ', IOuuid: ' + str(self.uuid))
            ESSDB.DB().action('IOqueue','UPD',('Status','114'),('work_uuid',self.uuid))
            self.run = 0
            #sys.exit(111)
        if self.run:
            ########################################################
            # Write AIP package to disk
            ########################################################
            self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            try:
                logger.info('Try to write %s to storage method disk target: %s, IOuuid: %s', self.ObjectIdentifierValue, self.sm_target, self.uuid)
                shutil.copy2(self.ObjectPath,self.sm_target)
                shutil.copy2(self.PMetaObjectPath,self.sm_target)
                if self.AICmets_objpath is not None:
                    shutil.copy2(self.AICmets_objpath,self.sm_target)
            except (IOError,os.error), why:
                logger.error('Problem to write %s to storage method disk target: %s, IOuuid: %s', self.ObjectIdentifierValue, self.sm_target, self.uuid)
                ESSDB.DB().action('IOqueue','UPD',('Status','115'),('work_uuid',self.uuid))
            else:
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                ##########################
                # Insert StorageTable
                storage_obj = storage()
                storage_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                storage_obj.contentLocationType = 200
                storage_obj.contentLocationValue = self.sm_target
                storage_obj.storageMediumID = 'disk'
                storage_obj.storageMediumUUID = storageMedium_obj
                storage_obj.ObjectUUID = ArchiveObject_obj
                #storage_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                storage_obj.LocalDBdatetime = self.timestamp_utc
                storage_obj.save()

#                res,errno,why = ESSDB.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
#                                                                           'contentLocationType','200',
#                                                                           'contentLocationValue',self.sm_target,
#                                                                           'storageMediumID','disk',
#                                                                           'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                if errno: logger.error('Failed to insert to Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
#                if errno == 0 and ExtDBupdate:
                if ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageTable,'INS',('ObjectIdentifierValue',self.ObjectIdentifierValue,
                                                                                              'contentLocationType','200',
                                                                                              'contentLocationValue',self.sm_target,
                                                                                              'storageMediumID','disk'))
                    if ext_errno: logger.error('Failed to insert to External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                    else:
                        #storage_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                        storage_obj.ExtDBdatetime = self.timestamp_utc
                        storage_obj.save(update_fields=['ExtDBdatetime'])
#                        res,errno,why = ESSDB.DB().action(self.StorageTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                                  ('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND',
#                                                                                   'contentLocationType','200','AND',
#                                                                                   'contentLocationValue',self.sm_target,'AND',
#                                                                                   'storageMediumID','disk'))
#                        if errno: logger.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                ##########################
                # Update StorageMediumTable
                storageMedium_obj.storageMediumUsedCapacity = self.new_target_size
                #storageMedium_obj.storageMediumDate = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.storageMediumDate = self.timestamp_utc
                storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                #storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.LocalDBdatetime = self.timestamp_utc
                storageMedium_obj.save(update_fields=['storageMediumUsedCapacity','storageMediumDate','linkingAgentIdentifierValue','LocalDBdatetime'])           
#                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_target_size,
#                                                                                 'storageMediumDate',self.timestamp_utc.replace(tzinfo=None),
#                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
#                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                                ('storageMediumID','disk'))
#                if errno: logger.error('Failed to update Local DB: ' + str('disk') + ' error: ' + str(why))
#                if errno == 0 and ExtDBupdate:
                if ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumUsedCapacity',self.new_target_size,
                                                                                                    'storageMediumDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                   ('storageMediumID','disk'))
                    if ext_errno: logger.error('Failed to update External DB: ' + str('disk') + ' error: ' + str(ext_why))
                    else:
                        #storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                        storageMedium_obj.ExtDBdatetime = self.timestamp_utc
                        storageMedium_obj.save(update_fields=['ExtDBdatetime'])
#                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID','disk'))
#                        if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                if storage.objects.filter(ObjectUUID__ObjectIdentifierValue=self.ObjectIdentifierValue, storageMediumUUID__storageMediumID='disk').exists():
#                if ESSDB.DB().action(self.StorageTable,'GET',('id',),('ObjectIdentifierValue',self.ObjectIdentifierValue,'AND','storageMediumID','disk')):
                    self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    self.writetime = self.stopTime-self.startTime
                    self.writesize = int(self.WriteSize)/1048576
                    if self.writetime.seconds < 1: self.writetime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                    self.MBperSEC = int(self.writesize)/int(self.writetime.seconds)
                    logger.info('Succedd to write IOuuid: %s for Object: %s to disk (%s MB/Sec)',str(self.uuid), self.ObjectIdentifierValue, str(self.MBperSEC))
                    ESSDB.DB().action('IOqueue','UPD',('Status','20'),('work_uuid',self.uuid))

    "Read IOuuid from disk"
    ###############################################
    def ReadDiskProc(self,uuid,ObjectIdentifierValue,ObjectPath,ObjectMessageDigest,sm_list):
        self.run = 1
        self.process_name = multiprocessing.current_process().name
        self.process_pid = multiprocessing.current_process().pid
        self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
        self.uuid = uuid
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.ObjectPath = ObjectPath
        self.ObjectMessageDigest = ObjectMessageDigest
        self.MessageDigestAlgorithm = ESSDB.DB().action(self.IngestTable,'GET',('ObjectMessageDigestAlgorithm',),('ObjectIdentifierValue',self.ObjectIdentifierValue))[0][0]
        self.sm_type = sm_list[0]
        self.sm_format = sm_list[1]
        self.sm_blocksize = sm_list[2]
        self.sm_maxCapacity = sm_list[3]
        self.sm_minChunkSize = sm_list[4]
        self.sm_minContainerSize = sm_list[5]
        self.sm_target = sm_list[6]
        self.sm_location = sm_list[7]
        self.sm_contentLocationValue = sm_list[8]

        logger.debug('ReadDiskProc start with IOuuid: %s, Object: %s, ObjectPath: %s, sm_list: %s, name: %s, pid: %s', self.uuid, self.ObjectIdentifierValue, self.ObjectPath, str(sm_list), self.process_name, self.process_pid)
        logger.info('Start Disk Read Process for object: %s, IOuuid: %s', self.ObjectIdentifierValue,self.uuid)
        ESSDB.DB().action('IOqueue','UPD',('Status','5'),('work_uuid',self.uuid))
        self.extractdir, self.ObjectFilename = os.path.split(self.ObjectPath)
        self.PMetaObjectFilename = self.ObjectFilename[:-4] + '_Package_METS.xml'
        # AIC fix - start
        status_code, info_list, self.AIC_UUID = ESSPGM.DB().GetAIC(self.ObjectIdentifierValue)
        if status_code > 0:
            logging.warning('Problem to get AIC info for ObjectUUID: %s, code: %s, info: %s' % (self.ObjectIdentifierValue,status_code,str(info_list)))
        else:
            logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
        self.AICmets_objFilename = self.AIC_UUID + '_AIC_METS.xml'
        # AIC fix - end
        self.tmpextractdir = os.path.join(self.extractdir,'.tmpextract')
        # Check write access to DIP directory
        if not os.access(self.extractdir, 7):
            ESSDB.DB().action('IOqueue','UPD',('Status','114'),('work_uuid',self.uuid))
            self.event_info = 'Problem to access DIP directory: %s, IOuuid: %s' % (self.extractdir, self.uuid)
            logger.error(self.event_info)
            ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
            self.run = 0
            #sys.exit(111)
        # Check if temp DIP directory exist, if not create tempDIR
        if self.run and not os.path.exists(self.tmpextractdir):
            os.mkdir(self.tmpextractdir)
        if self.run:
            ########################################################
            # Get AIP package to DIP directory
            ########################################################
            try:
                logger.info('Try to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s', self.ObjectIdentifierValue, self.sm_contentLocationValue, self.tmpextractdir,  self.uuid)
                self.SM_obj_disk_source = os.path.join(self.sm_contentLocationValue,self.ObjectFilename)
                self.SM_meta_disk_source = os.path.join(self.sm_contentLocationValue,self.PMetaObjectFilename)
                self.tmpDIP_obj_disk_target = os.path.join(self.tmpextractdir,self.ObjectFilename)
                self.tmpDIP_meta_disk_target = os.path.join(self.tmpextractdir,self.PMetaObjectFilename)
                shutil.copy2(self.SM_obj_disk_source,self.tmpDIP_obj_disk_target)
                shutil.copy2(self.SM_meta_disk_source,self.tmpDIP_meta_disk_target)
                if self.sm_format == 103:
                    self.SM_AIC_disk_source = os.path.join(self.sm_contentLocationValue,self.AICmets_objFilename)
                    self.tmpDIP_AIC_disk_target = os.path.join(self.tmpextractdir,self.AICmets_objFilename)
                    shutil.copy2(self.SM_AIC_disk_source,self.tmpDIP_AIC_disk_target)
            except (IOError,os.error), why:
                ESSDB.DB().action('IOqueue','UPD',('Status','115'),('work_uuid',self.uuid))
                self.event_info = 'Problem to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s, Error: %s' % (self.ObjectIdentifierValue, self.sm_contentLocationValue, self.tmpextractdir, self.uuid, str(why))
                logger.error(self.event_info)
                ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.run = 0
            else:
                self.event_info = 'Success to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s' % (self.ObjectIdentifierValue, self.sm_contentLocationValue, self.tmpextractdir,  self.uuid)
                logger.info(self.event_info)
                ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
        if self.run:
            #############################################
            # Checksum Check
            #############################################
            self.tp_sum,errno,why = ESSPGM.Check().checksum(self.tmpDIP_obj_disk_target,self.MessageDigestAlgorithm) # Checksum
            if errno:
                ESSDB.DB().action('IOqueue','UPD',('Status','116'),('work_uuid',self.uuid))
                self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.tmpDIP_obj_disk_target,str(why))
                logger.error(self.event_info)
                ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.run = 0
            else:
                self.event_info = 'Success to get checksum for: %s, Checksum: %s' % (self.tmpDIP_obj_disk_target,self.tp_sum)
                logger.info(self.event_info)
                ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
        if self.run:
            if str(self.tp_sum) == str(self.ObjectMessageDigest):
                self.event_info = 'Success to verify checksum for Object %s in tmpDIP: %s, IOuuid: %s' % (self.ObjectIdentifierValue, self.tmpextractdir, self.uuid)
                logger.info(self.event_info)
                ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
            else:
                self.event_info = 'Checksum verify mismatch for Object %s in tmpDIP: %s, IOuuid: %s, tape_checksum: %s, meta_checksum: %s' % (self.ObjectIdentifierValue, self.tmpextractdir, self.uuid, self.tp_sum, self.ObjectMessageDigest)
                logger.error(self.event_info)
                ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.run = 0
        if self.run:
            #############################
            # Move files to req path
            #############################
            self.DIP_obj_disk_target = self.ObjectPath
            self.DIP_meta_disk_target = os.path.join(self.extractdir,self.PMetaObjectFilename)
            shutil.move(self.tmpDIP_obj_disk_target,self.DIP_obj_disk_target)
            shutil.move(self.tmpDIP_meta_disk_target,self.DIP_meta_disk_target)
            if self.sm_format == 103:
                self.DIP_AIC_disk_target = os.path.join(self.extractdir,self.AICmets_objFilename)
                shutil.move(self.tmpDIP_AIC_disk_target,self.DIP_AIC_disk_target)
            logger.info('Succedd to get IOuuid: %s for Object: %s from SM disk (* MB/Sec)',str(self.uuid), self.ObjectIdentifierValue)
            ESSDB.DB().action('IOqueue','UPD',('Status','20'),('work_uuid',self.uuid))
        else:
            logger.error('Checksum in tmpDIP: ' + str(self.tp_sum) + ' and in DB: ' + str(self.ObjectMessageDigest))
            ESSDB.DB().action('IOqueue','UPD',('Status','100'),('work_uuid',self.uuid))
            #sys.exit(100)

    ###############################################
    def CountUniqueSort(self,worklist):
        # Listar t_prefix i ordningen flest förekommande först
        self.worklist = []
        self.worklist_unique = []
        for self.i in worklist:
            self.worklist.append(self.i)
        for self.i in set(self.worklist):
            self.num=0
            for self.a in self.worklist:
                if self.i == self.a:
                    self.num+=1
            self.worklist_unique.append((self.i, self.num))
        self.result = sorted(self.worklist_unique, key=operator.itemgetter(1), reverse=1)
        return self.result

    ###############################################
    def CheckDirSize(self,path):
        self.size = 0
        for self.f in os.listdir(path):
            self.path = os.path.join(path,self.f)
            self.mode = os.stat(self.path)
            if stat.S_ISREG(self.mode[0]):                   # It's a file
                self.size = self.size + self.mode[6]
            elif stat.S_ISDIR(self.mode[0]):                 # It's a directory
                self.size = self.size + Functions().CheckDirSize(self.path)
        return self.size

    ###############################################
    def CheckFileSize(self,path):
        self.size = 0
        self.exitstatus = 0
        try:
            self.mode = os.stat(path)
            if stat.S_ISREG(self.mode[0]):                   # It's a file
                self.size = self.mode[6]
            elif stat.S_ISDIR(self.mode[0]):                 # It's a directory
                self.size = Functions().CheckDirSize(path)
            else:
                self.exitstatus = 2
        except(OSError),(errno, why):
            #print 'test',why,errno
            # errno 2: No such file or directory
            if int(errno) == 2:
                self.exitstatus = 1
            else:
                self.exitstatus = 10
        return self.size, self.exitstatus

    ###############################################
    def ReleaseTapeLock(self,lock_uuid):
        ###################################################
        # Release lock for tapedrive
        ###################################################
        res = 'Missing drivelock for: %s' % lock_uuid
        exitstatus = 1
        #flush_transaction()
        robotdrives_objs = robotdrives.objects.filter(drive_lock=lock_uuid)
        for robotdrives_obj in robotdrives_objs:
            robotdrives_obj.drive_lock=''
            robotdrives_obj.save(update_fields=['drive_lock'])
            res = 'Release drivelock for: %s' % lock_uuid
            exitstatus = 0
#        time.sleep(5)
#        flush_transaction()
#        robotdrives_objs = robotdrives.objects.filter(drive_lock=lock_uuid)
#        for robotdrives_obj in robotdrives_objs:
#            logger.warning('second try to remove lock_uuid: %s' % lock_uuid)
#            robotdrives_obj.drive_lock=''
#            robotdrives_obj.save(update_fields=['drive_lock'])
#    
#        self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
#        self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id',),('drive_lock',self.uuid))
#        if self.robotdrive:
#            self.drive_id = self.robotdrive[0][0]
#            res = 'Release drivelock for: ' + str(self.uuid)
#            exitstatus = 0
#            ESSDB.DB().action(self.RobotDrivesTable,'UPD',('drive_lock',''),('drive_id',self.drive_id))
#        else:
#            res = 'Missing drivelock for: ' + str(self.uuid)
#            exitstatus = 1
        return res, exitstatus 

def WriteDiskProc(uuid,ObjectIdentifierValue,ObjectPath,WriteSize,sm_list):
    return Functions().WriteDiskProc(uuid,ObjectIdentifierValue,ObjectPath,WriteSize,sm_list)

def ReadDiskProc(uuid,ObjectIdentifierValue,ObjectPath,ObjectMessageDigest,sm_list):
    return Functions().ReadDiskProc(uuid,ObjectIdentifierValue,ObjectPath,ObjectMessageDigest,sm_list)

def WriteTapeProc(t_prefix,ActiveTapeIOs,ProcName):
    return Functions().WriteTapeProc(t_prefix,ActiveTapeIOs,ProcName)

def ReadTapeProc(t_id,ActiveTapeIOs,ProcName):
    return Functions().ReadTapeProc(t_id,ActiveTapeIOs,ProcName)

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        self.writeproc1 = 0
        self.writeproc2 = 0
        self.cmd20_p1_flag=0
        self.cmd20_p2_flag=0
        # Start disk IO pool with 2 process
        self.DiskIOtags = 2
        self.DiskIOpool = multiprocessing.Pool(self.DiskIOtags)
        # Start tape IO pool 
        # with 4 process
        self.TapeIOprocess = 4
        # Read IOtags 4 (two more then write IO tags and pysical drives, if 2 drives reached EOT the two extra IO tags for tape quick verify)
        self.TapeReadIOtags = 4
        # Write IOtags 2
        self.TapeWriteIOtags = 2
        self.TapeIOpool = multiprocessing.Pool(self.TapeIOprocess)
        self.ActiveTapeIOs = multiprocessing.Manager().list([])
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            db.close_old_connections()
            self.Disk_stop = 0
            for self.worker in self.DiskIOpool._pool: 
                if not self.worker.is_alive(): 
                    self.Disk_stop = 1
                    logger.error('Problem with DiskIOprocess_name: %s, process_pid: %s, process_exitcode: %s',self.worker.name,self.worker.pid,self.worker.exitcode)
            self.Tape_stop = 0
            for self.worker in self.TapeIOpool._pool:
                if not self.worker.is_alive():
                    self.Tape_stop = 1
                    logger.error('Problem with TapeIOprocess_name: %s, process_pid: %s, process_exitcode: %s',self.worker.name,self.worker.pid,self.worker.exitcode)
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0' or self.Disk_stop == 1 or self.Tape_stop == 1:
                logger.info('Stopping ' + ProcName)
                if self.Disk_stop:
                    self.DiskIOpool.terminate()
                else:
                    self.DiskIOpool.close()
                if self.Tape_stop:
                    self.TapeIOpool.terminate()
                else:
                    self.TapeIOpool.close()
                self.DiskIOpool.join()
                self.TapeIOpool.join()
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                time.sleep(1)
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()
            #self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
            #self.PolicyTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','PolicyTable'))[0][0]
            #self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
            #self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
            #self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
            #self.RobotReqTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotReqTable'))[0][0]
            #self.NumReadTapeDrives=2
            #self.NumWriteTapeDrives=2

            self.NumStatus0=0
            self.NumStatus5=0
            self.cmd10_flag=0
            self.cmd10_t_prefix=[]
            self.cmd15_flag=0
            self.cmd15_t_prefix=[]
            self.cmd20_flag=0
            self.cmd20_t_id=[]
            self.cmd25_flag=0
            self.cmd25_t_prefix=[]
            self.worklist,errno,why = ESSDB.DB().action('IOqueue','GET4',('ObjectIdentifierValue','cmd','cmdprio','work_uuid','ObjectPath',
                                                                          'WriteSize','t_prefix','storageMediumID','ObjectMessageDigest','sm_list','Status'),
                                                                         ('Status','=',0))
            # Flag Write or Read flags
            for self.i in self.worklist:
                # cmd10, normal write to tape
                if self.i[1] == 10: 
                    self.cmd10_flag = 1 
                    self.cmd10_t_prefix.append(self.i[6])
                # cmd15, normal write to disk
                elif self.i[1] == 15:
                    self.cmd15_flag = 1
                # cmd20, normal read from tape
                elif self.i[1] == 20:
                    self.cmd20_flag = 1
                    self.cmd20_t_id.append(self.i[7])
                # cmd25, normal read from disk
                elif self.i[1] == 25:
                    self.cmd25_flag = 1

            #self.TotalNumTapedrives=len(ESSDB.DB().action(self.RobotDrivesTable,'GET',('num_mounts','drive_id')))      #Get total num of tape drives
            #self.AvailableNumTapedrives=len(ESSDB.DB().action(self.RobotDrivesTable,'GET',('num_mounts','drive_id'),('status','Ready')))      #Get Available num of tape drives
            for self.i in self.worklist:
                self.ObjectIdentifierValue = self.i[0]
                self.cmd = self.i[1]
                self.uuid = self.i[3]
                self.ObjectPath = self.i[4]
                self.WriteSize = self.i[5]
                self.ObjectMessageDigest = self.i[8]
                self.sm_list = eval(self.i[9])
                ##############################################################################################Y
                # if self.DiskIOpool._state == 0 then pool is working.
                if self.DiskIOpool._state == 0:
                    # Get active queue depth for self.DiskIOpool._cache.
                    self.DiskIOactv = len(self.DiskIOpool._cache)
                    ###########################################################################################
                    # If IOcmd == 25 (DiskRead) start DiskReadProcess
                    if 1 and self.cmd == 25:
                        # if self.cmd15_flag == 1 reserv one IOtag for writes, if self.cmd15_flag == 0 add up to 2 more IOcmds then maximum DiskIOtags to DiskIOpool.
                        if self.cmd15_flag == 1 and self.DiskIOactv < self.DiskIOtags-1 or self.cmd15_flag == 0 and self.DiskIOactv < self.DiskIOtags+2:
                            ESSDB.DB().action('IOqueue','UPD',('Status','2'),('work_uuid',self.uuid))
                            self.DiskIOpool.apply_async(ReadDiskProc, (self.uuid,self.ObjectIdentifierValue,self.ObjectPath,self.ObjectMessageDigest,self.sm_list))
                    ###########################################################################################
                    # If IOcmd == 15 (DiskWrite) start DiskWriteProcess
                    elif 1 and self.cmd == 15:
                        # if self.cmd25_flag == 1 reserv all DiskIOtags for read, if self.cmd25_flag == 0 add up to 2 more IOcmds then maximum DiskIOtags to DiskIOpool.
                        if self.cmd25_flag == 0 and self.DiskIOactv < self.DiskIOtags+2:
                            ESSDB.DB().action('IOqueue','UPD',('Status','2'),('work_uuid',self.uuid))
                            self.DiskIOpool.apply_async(WriteDiskProc, (self.uuid,self.ObjectIdentifierValue,self.ObjectPath,self.WriteSize,self.sm_list))
            logger.debug('DiskIOpool_cache: %r',self.DiskIOpool._cache)

            ##############################################################################################Y
            # if self.TapeIOpool._state == 0 then pool is working.
            if self.TapeIOpool._state == 0:
                ###########################################################################################
                # If self.cmd20_flag == 1 (TapeRead) start TapeReadProcess
                if 1 and self.cmd20_flag == 1:
                    self.cmd20_t_id_sorted = Functions().CountUniqueSort(self.cmd20_t_id)
                    for self.select_cmd20_t_id in self.cmd20_t_id_sorted:
                        # Get active queue depth for self.TapeIOpool._cache.
                        self.TapeIOactv = len(self.TapeIOpool._cache)
                        # Check if avilable TapeIOtags. Add two extra IOtags to self.TapeIOtags to make it posible to verify tapes when write tapes are full.
                        if self.TapeIOactv < self.TapeReadIOtags:
                            # Check if any TapeIO process for t_prefix already in progress..
                            #self.ActiveTapeIOs,errno,why = ESSDB.DB().action('IOqueue','GET4',('ObjectIdentifierValue','cmd','cmdprio','work_uuid'),
                            #                                                                  ('(','Status','=',2,'OR','Status','=',5,')','AND',
                            #                                                                   'storageMediumID','=',self.select_cmd20_t_id[0],'AND',
                            #                                                                   'cmd','=',20))
                            if not self.select_cmd20_t_id[0] in self.ActiveTapeIOs:
                                for self.ii in self.worklist:
                                    if self.ii[1] == 20 and self.ii[7] == self.select_cmd20_t_id[0]:
                                        ESSDB.DB().action('IOqueue','UPD',('Status','2'),('work_uuid',self.ii[3]))
                                self.ActiveTapeIOs.append(self.select_cmd20_t_id[0])
                                self.TapeIOpool.apply_async(ReadTapeProc, (self.select_cmd20_t_id[0],self.ActiveTapeIOs,ProcName))
                                logging.info('Apply new read IO process for tape: %s, (ActiveTapeIOs: %s)' % (str(self.select_cmd20_t_id[0]),str(self.ActiveTapeIOs))) 
                ###########################################################################################
                # If self.cmd10_flag == 1 (TapeWrite) and self.cmd20_flag == 0 (TapeRead) start TapeWriteProcess
                elif 1 and self.cmd10_flag == 1 and self.cmd20_flag == 0:
                    self.t_prefix_sorted = Functions().CountUniqueSort(self.cmd10_t_prefix)
                    for self.select_t_prefix in self.t_prefix_sorted:
                        # Get active queue depth for self.TapeIOpool._cache.
                        self.TapeIOactv = len(self.TapeIOpool._cache)
                        # Check if avilable TapeIOtags.
                        if self.TapeIOactv < self.TapeWriteIOtags:
                            # Check if any TapeIO process for t_prefix already in progress..
                            #self.ActiveTapeIOs,errno,why = ESSDB.DB().action('IOqueue','GET4',('ObjectIdentifierValue','cmd','cmdprio','work_uuid'),
                            #                                                                  ('(','Status','=',2,'OR','Status','=',5,')','AND',
                            #                                                                   't_prefix','=',self.select_t_prefix[0],'AND',
                            #                                                                   'cmd','=',10))
                            #if not self.ActiveTapeIOs: 
                            if not self.select_t_prefix[0] in self.ActiveTapeIOs: 
                                for self.ii in self.worklist:
                                    if self.ii[1] == 10 and self.ii[6] == self.select_t_prefix[0]:
                                        ESSDB.DB().action('IOqueue','UPD',('Status','2'),('work_uuid',self.ii[3]))
                                self.ActiveTapeIOs.append(self.select_t_prefix[0])
                                self.TapeIOpool.apply_async(WriteTapeProc, (self.select_t_prefix[0],self.ActiveTapeIOs,ProcName))
                                logging.info('Apply new write IO process for tape prefix: %s, (ActiveTapeIOs: %s)' % (str(self.select_t_prefix[0]),str(self.ActiveTapeIOs))) 
            logger.debug('TapeIOpool_cache: %r',self.TapeIOpool._cache)
            db.close_old_connections()
            time.sleep(1)
            self.mLock.release()
        time.sleep(10)
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
# Table: ESSProc with Name: IOEngine, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'IOEngine'
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
    MultiProc = 1
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
    
    #WriteDiskProc2('0084b50e-8ac4-102d-8001-001e4f38d237','A0007700','/store/SIP/A0007700.tar',78583,[200, 0, 0, 0, 1000000, 0, '/store/disk1', 'ITArkiv_Marieberg'])
    #WriteTapeProc('TSB', 'ITArkiv_Marieberg')
    #ReadTapeProc('TSB001', 'ITArkiv_Marieberg')

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            time.sleep(10) 
            break
        time.sleep(1)
    logger.info('test3: ' + str(x.RunFlag))
    del x

# ./IOEngine.py
