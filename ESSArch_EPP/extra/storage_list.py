#!/usr/bin/env /ESSArch/python27/bin/python
# -*- coding: UTF-8 -*-
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB

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

# own models etc
from configuration.models import ESSArchPolicy
from essarch.models import ArchiveObject

import django
django.setup()

from lxml import etree
import ESSMD
 
def check_storage():
    EL_root = etree.Element('needcopies')    
    Policy_obj_list = ESSArchPolicy.objects.filter(PolicyStat=1).all()
    for Policy_obj in Policy_obj_list:
        sm_obj_list = [[Policy_obj.sm_1, Policy_obj.sm_type_1, Policy_obj.sm_format_1, Policy_obj.sm_blocksize_1, 
                        Policy_obj.sm_maxCapacity_1, Policy_obj.sm_minChunkSize_1, Policy_obj.sm_minContainerSize_1, 
                        Policy_obj.sm_target_1],
                       [Policy_obj.sm_2, Policy_obj.sm_type_2, Policy_obj.sm_format_2, Policy_obj.sm_blocksize_2, 
                        Policy_obj.sm_maxCapacity_2, Policy_obj.sm_minChunkSize_2, Policy_obj.sm_minContainerSize_2, 
                        Policy_obj.sm_target_2],
                       [Policy_obj.sm_3, Policy_obj.sm_type_3, Policy_obj.sm_format_3, Policy_obj.sm_blocksize_3, 
                        Policy_obj.sm_maxCapacity_3, Policy_obj.sm_minChunkSize_3, Policy_obj.sm_minContainerSize_3, 
                        Policy_obj.sm_target_3],
                       [Policy_obj.sm_4, Policy_obj.sm_type_4, Policy_obj.sm_format_4, Policy_obj.sm_blocksize_4, 
                        Policy_obj.sm_maxCapacity_4, Policy_obj.sm_minChunkSize_4, Policy_obj.sm_minContainerSize_4, 
                        Policy_obj.sm_target_4],
                       ]
        ip_obj_list = ArchiveObject.objects.filter(PolicyId=Policy_obj.PolicyID, StatusProcess=3000, StatusActivity=0).all()
        for ip_obj in ip_obj_list:
            storage_obj_list = ip_obj.storage_set.all()
            sm_num = 0 
            for sm_obj in sm_obj_list:
                sm_num += 1
                if sm_obj[0] == 1:
                    storage_count = 0
                    storageMediumID_list = []
                    for storage_obj in storage_obj_list:
                        storageMedium_obj = storage_obj.storageMediumUUID
                        if str(sm_obj[1])[0] == '2': #Disk
                            if storageMedium_obj.storageMedium == sm_obj[1] and storageMedium_obj.storageMediumID == 'disk':
                                storage_count+=1
                                storageMediumID_list.append(storageMedium_obj.storageMediumID)
                        elif str(sm_obj[1])[0] == '3': #Tape
                            if storageMedium_obj.storageMedium == sm_obj[1] and storageMedium_obj.storageMediumID.startswith(sm_obj[7]):
                                storage_count+=1
                                storageMediumID_list.append(storageMedium_obj.storageMediumID)
                    if storage_count == 0:
                        EL_object = etree.SubElement(EL_root, 'object', attrib={'id':ip_obj.ObjectIdentifierValue,
                                                                                'target':sm_obj[7],
                                                                                })
                        print 'Missing storage entry for storage method number: %s, target: %s, for object: %s' % ( sm_num, sm_obj[7], ip_obj.ObjectIdentifierValue)
                        
                    elif storage_count == 1:
                        print 'Found storage entry for storage method number: %s, target: %s (%s), for object: %s' % ( sm_num, sm_obj[7], ','.join(str(e) for e in storageMediumID_list), ip_obj.ObjectIdentifierValue)
                    else:
                        print 'Warning found to many storage entry for storage method number: %s, target: %s (%s), for object: %s' % ( sm_num, sm_obj[7], ','.join(str(e) for e in storageMediumID_list), ip_obj.ObjectIdentifierValue)
    doc = etree.ElementTree(element=EL_root, file=None)
    ESSMD.writeToFile(doc,'/ESSArch/log/needcopies/needcopies.xml')

if __name__ == '__main__':
    check_storage()
