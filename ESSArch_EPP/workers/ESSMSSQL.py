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
#import pymssql,_mssql,sys,time,string
import pyodbc,sys,time,string

from django.conf import settings

DBuser = ''
DATABASES_dict = getattr(settings,'DATABASES_AIS',{})
if DATABASES_dict:
    default_db = DATABASES_dict.get('default',{})
    if default_db:
        DBuser = default_db.get('USER','RA2B_ES21rcH')
        DBpasswd = default_db.get('PASSWORD','x')
        DBname = default_db.get('NAME','Arkis2Balder')
        DBhost = default_db.get('HOST','10.100.9.2')
        DBport = default_db.get('PORT','1433')
        DBTDS_Version = default_db.get('TDS','7.2')
        DBdriver = default_db.get('DRIVER','SQL Server')     # must match entry in /etc/unixODBC/odbcinst.ini
if not DBuser:
    DBhost = '10.100.9.2'        
    DBuser = 'RA2B_ES21rcH'         
    DBpasswd = 'x'   
    DBname = 'Arkis2Balder'        
    DBport = '1433'
    DBTDS_Version = '7.2'
    DBdriver = 'SQL Server'     # must match entry in /etc/unixODBC/odbcinst.ini

DBquery_timeout = 60

Debug = 0

class DB:
    def dbstr(self,x):
        try:
            res = str(x)
        except UnicodeEncodeError:
            res = str(x.encode('iso-8859-1'))
        return res

    def action(self,table,action,columns=None,where=None):
        ############### GET #################
        if action == 'GET' or action == 'GET3':
            self.columns = ''
            if columns:
                self.a = 0
                for self.col in columns:
                    if self.a == 0:
                        self.columns = str(self.col)
                        self.order = str(self.col)
                    else:
                        self.columns = str(self.columns) + ',' + str(self.col)
                    self.a = self.a + 1
            else:
                self.columns = '*'
            if where:
                self.a = 0
                self.b = 1
                for self.w in where:
                    if self.a == 0:             #First argument
                        self.where = str(self.w)
                        self.a = 1              #Flag that first argument is passed
                    elif self.b == 0:           #First argument after "and" or "or"
                        self.where = str(self.where) + str(self.w)
                        self.b = 1
                    elif self.b == 1:           #Second argument
                        #self.where = str(self.where) + "='" + str(self.w) + "'"
                        self.where = str(self.where) + "='" + self.w + "'"
                        self.b = 2
                    elif self.b == 2:           #"and" or "or" argument
                        self.where = str(self.where) + ' ' + str(self.w) + ' '
                        self.b = 0
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ' ORDER BY ' + self.order +';'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' ORDER BY ' + self.order +';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            if action == 'GET3':
                #return self.execute,errno, why
                return self.execute,errno,str(why)+' SQL: ' + self.sql 
            else:
                return self.execute
        ############### GET2 #################
        if action == 'GET2' or action == 'GET4':
            self.columns = ''
            if columns: 
                self.a = 0
                for self.col in columns:
                    if self.a == 0:
                        self.columns = str(self.col)
                        self.order = str(self.col)
                    else:
                        self.columns = str(self.columns) + ',' + str(self.col)
                    self.a = self.a + 1
            else: 
                self.columns = '*'
            if where:
                self.a = 0
                self.b = 1
                for self.w in where:
                    if self.a == 0:		#First argument
                        self.where = str(self.w)
                        self.a = 1		#Flag that first argument is passed
                    else:
                        self.where += ' ' + str(self.w)
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ' ORDER BY ' + self.order +';'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' ORDER BY ' + self.order +';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            if action == 'GET4':
                #return self.execute,errno, why
                return self.execute,errno,str(why)+' SQL: ' + self.sql 
            else:
                return self.execute
        ############### GETlast #################
        if action == 'GETlast':
            self.columns = ''
            if columns:
                self.a = 0
                for self.col in columns:
                    if self.a == 0:
                        self.columns = str(self.col)
                        self.order = str(self.col)
                    else:
                        self.columns = str(self.columns) + ',' + str(self.col)
                    self.a = self.a + 1
            else:
                self.columns = '*'
            if where:
                self.a = 0
                self.b = 1
                for self.w in where:
                    if self.a == 0:             #First argument
                        self.where = str(self.w)
                        self.a = 1              #Flag that first argument is passed
                    else:
                        self.where += ' ' + str(self.w)
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ' ORDER BY ' + self.order +' DESC LIMIT 1;'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' ORDER BY ' + self.order +' DESC LIMIT 1;'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            return self.execute,errno,why
        ############### GETsum #################
        if action == 'GETsum':
            self.columns = ''
            if columns:
                self.a = 0
                for self.col in columns:
                    if self.a == 0:
                        self.columns = 'SUM(' + str(self.col) + ')'
                    else:
                        self.columns = str(self.columns) + ',' + 'SUM(' + str(self.col) + ')'
                    self.a = self.a + 1
            else:
                self.columns = '*'
            if where:
                self.a = 0
                self.b = 1
                for self.w in where:
                    if self.a == 0:             #First argument
                        self.where = str(self.w)
                        self.a = 1              #Flag that first argument is passed
                    else:
                        self.where += ' ' + str(self.w)
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ';'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            return self.execute,errno,why
        ############### UPDATE/INSERT #################
        if action == 'UPD':
            self.columns = ''
            if columns:
                self.a = 0
                self.b = 1
                for self.col in columns:
                    if self.a == 0:		#First argument
                        self.columns = DB().dbstr(self.col)
                        self.a = 1		#Flag that first argument is passed
                    elif self.b == 0:		#First argument (second)
                        self.columns = DB().dbstr(self.columns) + ' ,' + DB().dbstr(self.col)
                        self.b = 1
                    elif self.b == 1:		#Second argument
                        if self.col == None:
                            self.columns = DB().dbstr(self.columns) + "=NULL"
                        else:
                            self.columns = DB().dbstr(self.columns) + "='" + DB().dbstr(self.col) + "'"
                        self.b = 0
            if where:
                self.a = 0
                self.b = 1
                for self.w in where:
                    if self.a == 0:             #First argument
                        self.where = DB().dbstr(self.w)
                        self.a = 1              #Flag that first argument is passed
                    elif self.b == 0:           #First argument after "and" or "or"
                        self.where = DB().dbstr(self.where) + DB().dbstr(self.w)
                        self.b = 1
                    elif self.b == 1:           #Second argument
                        self.where = DB().dbstr(self.where) + "='" + DB().dbstr(self.w) + "'"
                        self.b = 2
                    elif self.b == 2:           #"and" or "or" argument
                        self.where = DB().dbstr(self.where) + ' ' + DB().dbstr(self.w) + ' '
                        self.b = 0
                if action == 'UPD': self.sql = 'UPDATE ' + table + ' SET ' + self.columns + ' WHERE ' + self.where + ';'
            else:
                if action == 'UPD': self.sql = 'UPDATE ' + table + ' SET ' + self.columns + ';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql,1)
            if Debug: print 'executeOutput:',self.execute
            #return self.execute,errno,why
            return self.execute,errno,str(why)+' SQL: ' + self.sql 

#        ############### UPDATE/INSERT #################
#        if action == 'INS':
#            self.columns = ''
#            self.values = ''
#            if columns:
#                if Debug: print 'columns:',columns
#                self.a = 1
#                self.aa = 1
#                self.b = 1
#                self.bb = 1
#                for self.col in columns:
#                    #First column
#                    if self.a == 1:             
#                        self.columns = '('+ str(self.col)
#                        self.a = 0              #Flag that first column is passed
#                    #First value
#                    elif self.b == 1:           
#                        self.values = "('" + str(self.col) + "'"
#                        self.b = 0              #Flag that first value is passed
#                    #column
#                    elif self.aa == 1:          
#                        self.columns = str(self.columns) + ', '+ str(self.col)
#                        self.aa = 0              #Flag that next argument is a "value"
#                        self.bb = 1              #Flag that next argument is a "value"
#                    #value 
#                    elif self.bb == 1:          
#                        self.values = str(self.values) + ", '" + str(self.col) + "'"
#                        self.aa = 1              #Flag that next argument is a "column"
#                        self.bb = 0              #Flag that next argument is a "column"
#                self.columns = str(self.columns) + ')'
#                self.values = str(self.values) + ')'
#                self.sql = 'INSERT INTO ' + table + ' ' + self.columns + ' VALUES ' + self.values +';'
#            if Debug: print 'sql:',self.sql
#            self.execute,errno,why = DB().CursorExecute(self.sql,1)
#            #self.execute,errno,why = '',1,''
#            if Debug: print 'executeOutput:',self.execute
#            if errno and Debug: print 'errno&why:',errno,why
#            return self.execute,errno,str(why)+' SQL: ' + self.sql 

        ############### UPDATE/INSERT #################
        if action == 'INS':
            self.columns = ''
            self.values = ''
            if columns:
                if Debug: print 'columns:',columns
                self.a = 1
                self.aa = 1
                self.b = 1
                self.bb = 1
                for self.col in columns:
                    #First column
                    if self.a == 1:
                        self.columns = ("(%s") % (self.col)
                        self.a = 0              #Flag that first column is passed
                    #First value
                    elif self.b == 1:
                        self.values = ("('%s'") % (self.col)
                        self.b = 0              #Flag that first value is passed
                    #column
                    elif self.aa == 1:
                        self.columns = ("%s, %s") % (self.columns,self.col)
                        self.aa = 0              #Flag that next argument is a "value"
                        self.bb = 1              #Flag that next argument is a "value"
                    #value
                    elif self.bb == 1:
                        if self.col == None:
                            self.values = ("%s, %s") % (self.values,'NULL')
                        else:
                            self.values = ("%s, '%s'") % (self.values,self.col)
                        self.aa = 1              #Flag that next argument is a "column"
                        self.bb = 0              #Flag that next argument is a "column"
                self.columns = self.columns + ')'
                self.values = self.values + ')'
                self.sql = 'INSERT INTO ' + table + ' ' + self.columns + ' VALUES ' + self.values +';'
            #if Debug: print 'sql:',self.sql.encode('iso-8859-1')
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql,1)
            #self.execute,errno,why = '',1,''
            if Debug: print 'executeOutput:',self.execute
            if errno and Debug: print 'errno&why:',errno,why
            return self.execute,errno,str(why)+' SQL: ' + self.sql

        ############### DELETE #################
        if action == 'DEL':
            self.columns = ''
            if columns == 'ALL':			#argument columns is where when delete
                self.sql = 'DELETE FROM ' + table + ';'
            elif columns and not columns == 'ALL':	#argument columns is where when delete
                self.a = 0
                self.b = 1
                for self.w in columns:		#argument columns is where when delete
                    if self.a == 0:             #First argument
                        self.where = str(self.w)
                        self.a = 1              #Flag that first argument is passed
                    elif self.b == 0:           #First argument after "and" or "or"
                        self.where = str(self.where) + str(self.w)
                        self.b = 1
                    elif self.b == 1:           #Second argument
                        self.where = str(self.where) + "='" + str(self.w) + "'"
                        self.b = 2
                    elif self.b == 2:           #"and" or "or" argument
                        self.where = str(self.where) + ' ' + str(self.w) + ' '
                        self.b = 0
                self.sql = 'DELETE FROM ' + table + ' WHERE ' + self.where + ';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql,1)
            if Debug: print 'executeOutput:',self.execute
            return self.execute,errno,why
            
    ###############################################
    def CursorExecute(self,sql,commit=0):
        try:
            #self.db=pymssql.connect(host=DBhost,user=DBuser,password=DBpasswd,database=DBname,timeout=DBquery_timeout,login_timeout=DBlogin_timeout)
            #self.db=pymssql.connect(host=DBhost,user=DBuser,password=DBpasswd,database=DBname)
            self.db=pyodbc.connect(
                       DRIVER=DBdriver,
                       SERVER=DBhost,
                       UID=DBuser,
                       PWD=DBpasswd,
                       DATABASE=DBname,
                       TIMEOUT=DBquery_timeout,
                       TDS_Version=DBTDS_Version,
                       PORT=DBport)
            self.cursor = self.db.cursor()
            #self.cursor.setinputsizes(10500)
            self.cursor.execute(sql)
            if commit: 
                self.db.commit()
        #except (pymssql.Warning), (why):
        except (pyodbc.Warning), (why):
            return '',1,why
        #except (pymssql.Error), (why):
        except (pyodbc.Error), (why):
            return '',2,why
        #except (_mssql.error), (why):
        #    return '',3,why
        else:
            #if Debug: print self.cursor.description
            try:
                if not commit:
                    self.result = self.cursor.fetchall()
                else:
                    self.result = ''
                self.db.close()
            except (pyodbc.Warning), (why):
                return '',3,why
            except (pyodbc.Error), (why):
                return '',4,why
            else:
                return self.result,0,''

###############################################
def escape_string(inputstring):
    outputstring = string.replace(inputstring,"'","''") 
    return outputstring

#Database('dir2','GET',('testcol1','col2'),('col2','22','and','col2','33','or','col2','test'))
#Database('testitable','GET',('testcol1','col2'),('col2','22'))
#Database('testitable','GET',('testcol1','col2'))
#Database('testitable','UPD',('testcol1','newvalue1','col2','newvalue2'),('col2','22','and','col2','33','or','col2','test'))
#Database('testitable','UPD',('testcol1','newvalue1','col2','newvalue2'))
#DB().action('dir2','INS',('path','pathvalue','status','statvalue'))
#DB().action('dir2','GET',('id',))
#print DB().action('dir2','GET',('id',),('id','201'))
#DB().action('dir2','DEL',('id','201'))
#DB().action('archive','GET2',('c69','c70','c71','c72','c73','c27'),('c69','>=','2007','and','c70','=','02','and','c71','=','32'))
#print DB().action('IngestObject','GETsum',('ObjectSize',),('PolicyId','=','1'))
#print DB().action('archtape','GET2',('t_id','status'),('t_id','LIKE','"GSU2%"'))

#print 'test1: ',DB().action('ArchivePackageDB','GET3',('projektkod_fk','a_obj'),('a_obj','A0005352'))[0]
#print 'test2: ',DB().action('ArchivePackageDB','GET3',('projektkod_fk','a_obj'),('a_obj','A0005352'))[1]
#print 'test3: ',DB().action('ArchivePackageDB','GET3',('projektkod_fk','a_obj'),('a_obj','A0005352'))[2]
#print 'test3: ',DB().action('IngestObject','GET3',('ObjectIdentifierValue','ObjectSize'),('ObjectIdentifierValue','A0005352'))
#print 'test3: ',DB().action('IngestObject','GET3',('ObjectIdentifierValue','ObjectSize'),('ObjectIdentifierValue','F0000556'))

#print DB().action('archtape','GET2',('t_id','status'),('id',)
#t_id='FB1002'
#StorageTable='storage'
#print int(DB().action('storage','GETlast',('contentLocationValue',),('storageMediumID','=','"'+t_id+'"'))[0][0]) + 1
#print int(DB().action(StorageTable,'GETlast',('contentLocationValue',),('storageMediumID','=','"'+t_id+'"'))[0][0]) + 1

