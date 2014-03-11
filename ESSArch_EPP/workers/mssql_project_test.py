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

import ESSMSSQL,uuid

class ais:
    #########################################
    def projekttest_old(self,DataObjectIdentifier):
        self.DataObjectIdentifier = DataObjectIdentifier
        self.Packagedbget,ext_errno,ext_why = ESSMSSQL.DB().action('ArchivePackageDB','GET3',('projektkod_fk','a_obj'),('a_obj',self.DataObjectIdentifier))
        if ext_errno:
            print 'ext_why: %s' % str(ext_why)
  
        if self.Packagedbget:
            self.Projektdbget = ESSMSSQL.DB().action('ArchiveProjektkodDB','GET',('Projektgrupp_fk','Projektgrupp_namn'),('projektkod_id',self.Packagedbget[0][0]))
            self.extPrjKod = self.Projektdbget[0][0]
            self.extPrjNamn = self.Projektdbget[0][1]
            print 'PrjKod: ' + str(self.extPrjKod) + ' PrjNamn: ' + str(self.extPrjNamn)

    #########################################
    def projekttest(self,ObjectIdentifierValue):
        Debug = 1
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.IngestTable = 'IngestObject'
#        self.extOBJdbget,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'GET3',('ProjectGroupCode',
#                                                                                           'ObjectPackageName',
#                                                                                           'ObjectGuid',
#                                                                                           'ObjectActive',
#                                                                                           'EntryDate',
#                                                                                           'EntryAgentIdentifierValue'),
#                                                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue))

        self.extOBJdbget,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'GET3',('ProjectGroupCode',
                                                                                           'ObjectPackageName',
                                                                                           'ObjectGuid',
                                                                                           'ObjectActive',
                                                                                           'EntryDate',
                                                                                           'EntryAgentIdentifierValue',
                                                                                           'OAISPackageType',
                                                                                           'preservationLevelValue',
                                                                                           'ProjectGroupName'),
                                                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue))


        if ext_errno: print ('Failed to access External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
        if not ext_errno and self.extOBJdbget:
            #if Debug: print ('self.extOBJdbget: '+str(self.extOBJdbget)+' for ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
            self.ext_ProjectGroupCode = self.extOBJdbget[0][0]
            self.ext_ObjectPackageName = self.extOBJdbget[0][1]
            #self.ext_ObjectGuid = uuid.UUID(bytes_le=self.extOBJdbget[0][2])       #When pymssql
            self.ext_ObjectGuid = uuid.UUID(self.extOBJdbget[0][2])
            self.ext_ObjectActive = self.extOBJdbget[0][3]
            self.ext_EntryDate = self.extOBJdbget[0][4]
            self.ext_EntryAgentIdentifierValue = self.extOBJdbget[0][5]
            self.ext_OAISPackageType = self.extOBJdbget[0][6]
            self.ext_preservationLevelValue = self.extOBJdbget[0][7]
            self.ext_ProjectGroupName = self.extOBJdbget[0][8]
            if Debug: print ('ext_ProjectGroupCode is: '+str(self.ext_ProjectGroupCode)+' for ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
            if Debug: print ('ext_ObjectActive is: '+str(self.ext_ObjectActive)+' for ObjectIdentifierValue '+str(self.ObjectIdentifierValue))
            return (self.ext_ProjectGroupCode,self.ext_ObjectPackageName,self.ext_ObjectGuid,self.ext_ObjectActive,self.ext_EntryDate,self.ext_EntryAgentIdentifierValue,self.ext_OAISPackageType,self.ext_preservationLevelValue,self.ext_ProjectGroupName),0,self.ObjectIdentifierValue
        return ('','','','','',''),1,'%s not found in ais' % self.ObjectIdentifierValue



#print ais().projekttest('00010688')
#print ais().projekttest('90000323')
#print ais().projekttest('90000311')
#print ais().projekttest('90000312')
#print ais().projekttest('90000313')
#print ais().projekttest('90000314')
#print ais().projekttest('90000315')
#print ais().projekttest('90000316')
#print ais().projekttest('90000317')
#print ais().projekttest('90000318')
#print ais().projekttest('90000319')
#print ais().projekttest('90000321')
#print ais().projekttest('90000322')
#print ais().projekttest('90000324')
#print ais().projekttest('A0000037')
#print ais().projekttest('A0005812')
#print ais().projekttest('H0000621')
#print ais().projekttest('H0000624')
#print ais().projekttest('H0000625')
#print ais().projekttest('H0000626')
#print ais().projekttest('H0000627')
#print ais().projekttest('L0000045')
#print ais().projekttest('L0000046')
#print ais().projekttest('U0000064')
#print ais().projekttest('V0000032')
#print ais().projekttest('V0000033')
#print ais().projekttest('V0000034')
#print ais().projekttest('V0000035')
#print ais().projekttest('V0000036')
#print ais().projekttest('V0000037')
#print ais().projekttest('V0000038')
#print ais().projekttest('A0020831')
#print ais().projekttest('C0025479')
#print ais().projekttest('A0032599')
#print ais().projekttest('A0032712')
#ais().projekttest_old(DataObjectIdentifier='A0033983')
#print ais().projekttest('A0007626')
print ais().projekttest('A0032714')
print ais().projekttest('Q0000101')
