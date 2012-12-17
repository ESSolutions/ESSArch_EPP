# -*- coding: utf-8 -*-
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
__revision__ = "$Revision: 43 $"
__date__ = "$Date: 2012-12-17 11:53:07 +0100 (Mon, 17 Dec 2012) $"
__author__ = "$Author: henrik $"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
################################################################################
# Note: Generated by soapbox.wsdl2py at 2012-08-29 22:52:39.923519
#       Try to avoid editing it if you might need to regenerate it.
################################################################################

############## extra start #####################################################
import sys, logging, logging.handlers, string,  ESSMSSQL, ESSPGM
from django.contrib.auth.decorators import permission_required
from django.contrib.auth import authenticate

ProcName = 'storageLogistics'
ProcVersion = __version__


LogLevel = 10
Console = 0
LogFile = '/ESSArch/log/storageLogistics.log'
##########################
# Log format
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
logging.getLogger('').setLevel(0)
logging.getLogger('').addHandler(essLocalFileHandler)
if Console: logging.getLogger('').addHandler(essConsoleHandler)
############## extra end #######################################################

from soapbox import soap, xsd
from soapbox.xsd import UNBOUNDED

################################################################################
# Schemas


# http://ESSArch_Instance.ra.se/StorageLogisticsService.xs


class StoragelogisticsResponse(xsd.ComplexType):
    '''
    '''
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    returncode = xsd.Element(xsd.Integer, nillable=True)

    @classmethod
    def create(cls, returncode):
        instance = cls()
        instance.returncode = returncode
        return instance


class StoragelogisticsRequest(xsd.ComplexType):
    '''
    '''
    INHERITANCE = None
    INDICATOR = xsd.Sequence
    storagemediumid = xsd.Element(xsd.String)
    eventtype = xsd.Element(xsd.Integer)
    storagemediumlocation = xsd.Element(xsd.String)
    storagemediumdestination = xsd.Element(xsd.String)
    useridentifiervalue = xsd.Element(xsd.String)
    userpassword = xsd.Element(xsd.String)
    eventdatetime = xsd.Element(xsd.String)

    @classmethod
    def create(cls, storagemediumid, eventtype, storagemediumlocation, storagemediumdestination, useridentifiervalue, userpassword, eventdatetime):
        instance = cls()
        instance.storagemediumid = storagemediumid
        instance.eventtype = eventtype
        instance.storagemediumlocation = storagemediumlocation
        instance.storagemediumdestination = storagemediumdestination
        instance.useridentifiervalue = useridentifiervalue
        instance.userpassword = userpassword
        instance.eventdatetime = eventdatetime
        return instance


Schema_55b49 = xsd.Schema(
    imports=[],
    targetNamespace='http://ESSArch_Instance.ra.se/StorageLogisticsService',
    elementFormDefault='unqualified',
    #elementFormDefault='qualified',
    #elementFormDefault=xsd.ElementFormDefault.UNQUALIFIED,
    #elementFormDefault=xsd.ElementFormDefault.QUALIFIED,
    simpleTypes=[],
    attributeGroups=[],
    groups=[],
    complexTypes=[],
    elements={'storagelogisticsResponse': xsd.Element(StoragelogisticsResponse()), 'storagelogisticsRequest': xsd.Element(StoragelogisticsRequest())},
)


################################################################################
# Operations

#@permission_required('StorageLogistics_ws.StorageLogistics')
def storagelogistics(request, storagelogisticsRequest):
    logging.debug('Request parameters before replace: storagemediumlocation=%s storagemediumdestination=%s useridentifiervalue=%s storagemediumid=%s eventtype=%s userpassword=%s eventdatetime=%s',storagelogisticsRequest.storagemediumlocation, storagelogisticsRequest.storagemediumdestination, storagelogisticsRequest.useridentifiervalue, storagelogisticsRequest.storagemediumid, storagelogisticsRequest.eventtype, storagelogisticsRequest.userpassword, storagelogisticsRequest.eventdatetime)
    ###################################
    # Replace "-" with "_"
    if storagelogisticsRequest.storagemediumlocation is not None:
        storagemediumlocation = string.replace(storagelogisticsRequest.storagemediumlocation,"-","_")
    else:
        storagemediumlocation = ''

    if storagelogisticsRequest.storagemediumdestination is not None:
        storagemediumdestination = string.replace(storagelogisticsRequest.storagemediumdestination,"-","_")
    else:
        storagemediumdestination = '' 

    if storagelogisticsRequest.useridentifiervalue is not None:
        useridentifiervalue = string.replace(storagelogisticsRequest.useridentifiervalue,"-","_")
    else:
        useridentifiervalue = ''
    ###################################
    # Separate MediumID and MediumVersion
    if storagelogisticsRequest.storagemediumid is not None:
        MediumID = storagelogisticsRequest.storagemediumid[:6]
        MediumVersion = storagelogisticsRequest.storagemediumid[6:]
    else:
        MediumID = ''
        MediumVersion = ''

    if storagelogisticsRequest.eventtype is not None: 
        eventtype = storagelogisticsRequest.eventtype
    else:
        eventtype = 99
    
    if storagelogisticsRequest.userpassword is not None:
        userpassword = storagelogisticsRequest.userpassword
    else:
        userpassword = ''

    eventdatetime = storagelogisticsRequest.eventdatetime

    logging.debug('Request parameters: storagemediumlocation=%s storagemediumdestination=%s useridentifiervalue=%s MediumID=%s MediumVersion=%s eventtype=%s userpassword=%s eventdatetime=%s',storagemediumlocation, storagemediumdestination, useridentifiervalue, MediumID, MediumVersion, eventtype, userpassword, eventdatetime)
    
    UserAuthMethod=0 # 0=local DB, 1=AIS
    UserAuth = 0
    if UserAuthMethod==0:
        ###################################
        # Check user in Django DB
        user = authenticate(username=useridentifiervalue, password=userpassword)
        if user is not None:
            if user.is_active:
                logging.info('You provided a correct username: %s and password!', useridentifiervalue)
                if user.has_perm('storagelogistics.StorageLogistics'):
                    logging.info('User %s is authorised',useridentifiervalue)
                    UserAuth = 1
                else:
                    logging.info('User %s is not authorised',useridentifiervalue)
                    return StoragelogisticsResponse(returncode=1)
            else:
                logging.info('Your account: %s has been disabled!', useridentifiervalue)
                return StoragelogisticsResponse(returncode=2)
        else:
            logging.info('Your username: %s and password were incorrect.', useridentifiervalue)
            return StoragelogisticsResponse(returncode=3)
        #print user.get_all_permissions(obj='StorageLogistics_ws')
        #print user.get_all_permissions()
    elif UserAuthMethod==1:
        ###################################
        # Check user in AIS
        res,errno,why = func().AuthorityCheck(useridentifiervalue)
        if errno == 0:
            if res[0] == 1:
                logging.info('User %s exist in AIS, verify password',useridentifiervalue)
                if userpassword == res[2]:
                    logging.info('User %s is authorised',useridentifiervalue)
                    UserAuth = 1
                else:
                    logging.info('User %s is not authorised',useridentifiervalue)
                    return StoragelogisticsResponse(returncode=1)
            elif res[0] == 0:
                logging.info('User %s not found in AIS',useridentifiervalue)
                return StoragelogisticsResponse(returncode=2)
        else:
            logging.error('Problem to check authority for user: %s , errno: %s , why: %s',useridentifiervalue,errno,why)
            return StoragelogisticsResponse(returncode=3)

    #return StoragelogisticsResponse(returncode=999)

    #####################################
    # Check medium status
    LocationStatus = 0
    res,errno,why = func().MediumStatusCheck(MediumID)
    if errno == 0:
        LocationStatus = res[0]
        CurrentStorageMediumLocation = res[1]
        if LocationStatus == 10:
            logging.info('LocationStatus for MediumID %s is "Levererad"',MediumID)
        elif LocationStatus == 20:
            logging.info('LocationStatus for MediumID %s is "Mottagen"',MediumID)
        elif LocationStatus == 30:
            logging.info('LocationStatus for MediumID %s is "Placerad"',MediumID)
        elif LocationStatus == 40:
            logging.info('LocationStatus for MediumID %s is "Uttagen"',MediumID)
        elif LocationStatus == 50:
            logging.info('LocationStatus for MediumID %s is "Robot"',MediumID)
        elif LocationStatus == 60:
            logging.info('LocationStatus for MediumID %s is "Disk"',MediumID)
        else:
            logging.info('LocationStatus for MediumID %s is "Unknown?" (%s)',MediumID,LocationStatus)
    elif errno == 1:
        logging.error('Problem to check LocationStatus in AIS for MediumID: %s , errno: %s , why: %s',MediumID,errno,why)
        return StoragelogisticsResponse(returncode=4)
    elif errno == 2:
        logging.error('MediumID %s is not unique in AIS! errno: %s , why: %s',MediumID,errno,why)
        return StoragelogisticsResponse(returncode=5)
    elif errno == 3:
        logging.info('MediumID %s was not found in AIS! errno: %s , why: %s',MediumID,errno,why)
        return StoragelogisticsResponse(returncode=6)

    storageMedium_table = 'storageMedium'

    # worker code method
    ########################################################################
    if eventtype == 10:     #Leverans
        if UserAuth and not CurrentStorageMediumLocation == storagemediumlocation:
            logdetail = 'Skip to update LocationStatus to 10 for MediumID: %s because present Location is %s' % (MediumID,CurrentStorageMediumLocation)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('10','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=storagemediumdestination,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=14)
            else:
                return StoragelogisticsResponse(returncode=13)
        if UserAuth and CurrentStorageMediumLocation == storagemediumlocation and not LocationStatus ==  10:
            errno,why = ESSPGM.DB().SetStorageMediumLocation(local_table=storageMedium_table, ext_table=storageMedium_table, AgentIdentifierValue=useridentifiervalue, storageMediumID=MediumID, storageMediumLocation=storagemediumlocation, storageMediumLocationStatus=eventtype, storageMediumDate=eventdatetime)
            #res,errno,why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumLocationStatus',10,
            #                                                            'storageMediumDate',eventdatetime,
            #                                                            'linkingAgentIdentifierValue',useridentifiervalue),
            #                                                           ('storageMediumID',MediumID))
            if errno:
                logging.error('Failed to update AIS for MediumID: %s , error: %s',MediumID,str(why))
                return StoragelogisticsResponse(returncode=11)
            else:
                logdetail = 'Succeeded to update LocationStatus to 10 for MediumID: %s' % (MediumID)
                logging.info(logdetail)
                rc = ESSPGM.Events().create('10','','ESSArch StorageLogistics',ProcVersion,'0',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=storagemediumdestination,RelatedEventIdentifierValue=None)
                if rc:
                    logging.error('Failed to create event for MediumID: %s',MediumID)
                    return StoragelogisticsResponse(returncode=12)
                else:
                    logging.info('Succeeded to create event for MediumID: %s',MediumID)
            return StoragelogisticsResponse(returncode=0)
        else:
            logdetail = 'Skip to update LocationStatus to 10 for MediumID: %s because present LocationStatus is %s' % (MediumID,LocationStatus)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('10','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=storagemediumdestination,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=15)
            else:
                return StoragelogisticsResponse(returncode=10)
    ########################################################################
    elif eventtype == 20:   #Mottagning
        #####################################
        # Delivery Check
        RelatedEventIdentifierValue = None
        res,errno,why = func().DeliveryCheck(MediumID,storagemediumlocation)
        if errno == 0:
            RelatedEventIdentifierValue = res[0]
        elif errno == 1:
            logging.error('Problem to delivery check MediumID: %s , errno: %s , why: %s',MediumID,errno,why)
            return StoragelogisticsResponse(returncode=23)
        elif errno == 2:
            logging.error('Found more then one delivery event for MediumID %s in AIS! errno: %s , why: %s',MediumID,errno,why)
            return StoragelogisticsResponse(returncode=24)
        elif errno == 3:
            logging.info('Delivery event for MediumID %s was not found in AIS! errno: %s , why: %s',MediumID,errno,why)
            return StoragelogisticsResponse(returncode=25)
        if UserAuth and LocationStatus ==  10:
            errno,why = ESSPGM.DB().SetStorageMediumLocation(local_table=storageMedium_table, ext_table=storageMedium_table, AgentIdentifierValue=useridentifiervalue, storageMediumID=MediumID, storageMediumLocation=storagemediumlocation, storageMediumLocationStatus=eventtype, storageMediumDate=eventdatetime)
            #res,errno,why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumLocationStatus',20,
            #                                                            'storageMediumLocation',storagemediumlocation,
            #                                                            'storageMediumDate',eventdatetime,
            #                                                            'linkingAgentIdentifierValue',useridentifiervalue),
            #                                                           ('storageMediumID',MediumID))
            if errno:
                logging.error('Failed to update AIS for MediumID: %s , error: %s',MediumID,str(why))
                return StoragelogisticsResponse(returncode=21)
            else:
                logdetail = 'Succeeded to update LocationStatus to 20 for MediumID: %s' % (MediumID)
                logging.info(logdetail)
                rc = ESSPGM.Events().create('20','','ESSArch StorageLogistics',ProcVersion,'0',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=RelatedEventIdentifierValue)
                if rc:
                    logging.error('Failed to create event for MediumID: %s',MediumID)
                    return StoragelogisticsResponse(returncode=22)
                else:
                    logging.info('Succeeded to create event for MediumID: %s',MediumID)
            return StoragelogisticsResponse(returncode=0)
        else:
            logdetail = 'Skip to update LocationStatus to 20 for MediumID: %s because present LocationStatus is %s' % (MediumID,LocationStatus)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('20','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=RelatedEventIdentifierValue)
            if rc:
                return StoragelogisticsResponse(returncode=26)
            else:
                return StoragelogisticsResponse(returncode=20)
    ########################################################################
    elif eventtype == 30:   #Placering
        if UserAuth and not CurrentStorageMediumLocation == storagemediumlocation:
            logdetail = 'Skip to update LocationStatus to 30 for MediumID: %s because present Location is %s' % (MediumID,CurrentStorageMediumLocation)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('30','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=storagemediumdestination,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=34)
            else:
                return StoragelogisticsResponse(returncode=33)
        if UserAuth and CurrentStorageMediumLocation == storagemediumlocation and not (LocationStatus == 30 or LocationStatus == 10):
            errno,why = ESSPGM.DB().SetStorageMediumLocation(local_table=storageMedium_table, ext_table=storageMedium_table, AgentIdentifierValue=useridentifiervalue, storageMediumID=MediumID, storageMediumLocation=storagemediumlocation, storageMediumLocationStatus=eventtype, storageMediumDate=eventdatetime)
            #res,errno,why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumLocationStatus',30,
            #                                                            'storageMediumDate',eventdatetime,
            #                                                            'linkingAgentIdentifierValue',useridentifiervalue),
            #                                                           ('storageMediumID',MediumID))
            if errno:
                logging.error('Failed to update AIS for MediumID: %s , error: %s',MediumID,str(why))
                return StoragelogisticsResponse(returncode=31)
            else:
                logdetail = 'Succeeded to update LocationStatus to 30 for MediumID: %s' % (MediumID)
                logging.info(logdetail)
                rc = ESSPGM.Events().create('30','','ESSArch StorageLogistics',ProcVersion,'0',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=None)
                if rc:
                    logging.error('Failed to create event for MediumID: %s',MediumID)
                    return StoragelogisticsResponse(returncode=32)
                else:
                    logging.info('Succeeded to create event for MediumID: %s',MediumID)
            return StoragelogisticsResponse(returncode=0)
        else:
            logdetail = 'Skip to update LocationStatus to 30 for MediumID: %s because present LocationStatus is %s' % (MediumID,LocationStatus)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('30','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=35)
            else:
                return StoragelogisticsResponse(returncode=30)
    ########################################################################
    elif eventtype == 40:   #Uttag
        if UserAuth and not CurrentStorageMediumLocation == storagemediumlocation:
            logdetail = 'Skip to update LocationStatus to 40 for MediumID: %s because present Location is %s' % (MediumID,CurrentStorageMediumLocation)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('40','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=storagemediumdestination,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=44)
            else:
                return StoragelogisticsResponse(returncode=43)
        if UserAuth and CurrentStorageMediumLocation == storagemediumlocation and LocationStatus ==  30:
            errno,why = ESSPGM.DB().SetStorageMediumLocation(local_table=storageMedium_table, ext_table=storageMedium_table, AgentIdentifierValue=useridentifiervalue, storageMediumID=MediumID, storageMediumLocation=storagemediumlocation, storageMediumLocationStatus=eventtype, storageMediumDate=eventdatetime)
            #res,errno,why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumLocationStatus',40,
            #                                                            'storageMediumDate',eventdatetime,
            #                                                            'linkingAgentIdentifierValue',useridentifiervalue),
            #                                                           ('storageMediumID',MediumID))
            if errno:
                logging.error('Failed to update AIS for MediumID: %s , error: %s',MediumID,str(why))
                return StoragelogisticsResponse(returncode=41)
            else:
                logdetail = 'Succeeded to update LocationStatus to 40 for MediumID: %s' % (MediumID)
                logging.info(logdetail)
                rc = ESSPGM.Events().create('40','','ESSArch StorageLogistics',ProcVersion,'0',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=None)
                if rc:
                    logging.error('Failed to create event for MediumID: %s',MediumID)
                    return StoragelogisticsResponse(returncode=42)
                else:
                    logging.info('Succeeded to create event for MediumID: %s',MediumID)
            return StoragelogisticsResponse(returncode=0)
        else:
            logdetail = 'Skip to update LocationStatus to 40 for MediumID: %s because present LocationStatus is %s' % (MediumID,LocationStatus)
            logging.warning(logdetail)
            rc = ESSPGM.Events().create('40','','ESSArch StorageLogistics',ProcVersion,'1',logdetail,2,storageMediumID=MediumID,eventDateTime=eventdatetime,linkingAgentIdentifierValue=useridentifiervalue,storageMediumLocation=storagemediumlocation,storageMediumDestination=None,RelatedEventIdentifierValue=None)
            if rc:
                return StoragelogisticsResponse(returncode=45)
            else:
                return StoragelogisticsResponse(returncode=40)
    ########################################################################
    elif eventtype == 50:
        return StoragelogisticsResponse(returncode=50)
    return StoragelogisticsResponse(returncode=99)
    #return storagelogisticsResponse

class func:
    "AuthorityCheck"
    ###############################################
    def AuthorityCheck(self,username):
        table = 'storageUser'
        rows,errno,why = ESSMSSQL.DB().action(table,'GET3',('userIdentifierValue','userPassword','userRight'),('userIdentifierValue',username))
        if not errno:
            if len(rows) == 1:
                return [1,rows[0][0],rows[0][1],rows[0][2]], 0, str(why)
            elif len(rows) > 1:
                return [0,username,'none','none'],2,'Username %s is not unique! dbres: %s , why: %s' % (username,str(rows),str(why))
            else:
                return [0,username,'none','none'], 0, str(why)
        else:
            return [0,'none','none','none'], 1, str(why)

    "MediumStatusCheck"
    ###############################################
    def MediumStatusCheck(self,storageMediumID):
        table = 'storageMedium'
        rows,errno,why = ESSMSSQL.DB().action(table,'GET3',('storageMediumLocationStatus','storageMediumLocation'),('storageMediumID',storageMediumID))
        if not errno:
            if len(rows) == 1:
                return [rows[0][0],rows[0][1],storageMediumID], 0, str(why)
            elif len(rows) > 1:
                return [0,storageMediumID],2,'storageMediumID %s is not unique! dbres: %s , why: %s' % (storageMediumID,str(rows),str(why))
            else:
                return [0,storageMediumID],3,'storageMediumID %s not found! dbres: %s , why: %s' % (storageMediumID,str(rows),str(why))
        else:
            return [0,'none'], 1, str(why)

    "DeliveryCheck"
    ###############################################
    def DeliveryCheck(self,storageMediumID,storagemediumlocation):
        table = 'eventStorageMediumSource'
        rows,errno,why = ESSMSSQL.DB().action(table,'GET3',('eventIdentifierValue',),('eventType','10','AND','eventOutcome','0','AND','storageMediumID',storageMediumID,'AND','storageMediumDestination',storagemediumlocation))
        if not errno:
            if len(rows) == 1:
                return [rows[0][0],storageMediumID], 0, str(why)
            elif len(rows) > 1:
                return [None,storageMediumID],2,'storageMediumID %s is not unique! dbres: %s , why: %s' % (storageMediumID,str(rows),str(why))
            else:
                return [None,storageMediumID],3,'storageMediumID %s not found! dbres: %s , why: %s' % (storageMediumID,str(rows),str(why))
        else:
            return [None,'none'], 1, str(why)



################################################################################
# Methods


storagelogistics_method = xsd.Method(function=storagelogistics,
    soapAction='http://ESSArch_Instance.ra.se/StorageLogisticsService/storagelogistics',
    input='storagelogisticsRequest',
    inputPartName='parameters',
    output='storagelogisticsResponse',
    outputPartName='parameters',
    operationName='storagelogistics',
)


################################################################################
# SOAP Service


StorageLogisticsService_Port_SERVICE = soap.Service(
    name='StorageLogisticsService_Port',
    targetNamespace='http://ESSArch_Instance.ra.se/StorageLogisticsService',
    location='%(scheme)s://%(host)s/webservice/StorageLogisticsService',
    #location='http://ESSArch_Instance.ra.se/webservice/StorageLogisticsService',
    schema=Schema_55b49,
    version=soap.SOAPVersion.SOAP11,
    methods=[storagelogistics_method],
)


################################################################################
# Django Dispatch


# Uncomment these lines to turn on dispatching:
from django.views.decorators.csrf import csrf_exempt
dispatch = csrf_exempt(soap.get_django_dispatch(StorageLogisticsService_Port_SERVICE))

# Put these lines in the urls.py file of your Django project/application:
#urlpatterns += patterns('',
#    (r'^webservice/StorageLogisticsService$', '<module>.dispatch'),
#)

################################################################################
# vim:et:ft=python:nowrap:sts=4:sw=4:ts=4
