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
import MySQLdb 

from django.conf import settings

DBuser = ''
DATABASES_dict = getattr(settings,'DATABASES',{})
if DATABASES_dict:
    default_db = DATABASES_dict.get('default',{})
    if default_db.get('ENGINE','').find('mysql') > -1:
        DBuser = default_db.get('USER','arkiv')
        DBpasswd = default_db.get('PASSWORD','password')
        DBname = default_db.get('NAME','essarch')
if not DBuser:
    DBuser = 'arkiv'
    DBpasswd = 'password'
    DBname = 'essarch'

Debug = 0

class DB:
    def dbstr(self,x):
        try:
            res = str(x)
        except UnicodeEncodeError:
            res = str(x.encode('iso-8859-1'))
            # NRA special solution to translate "DASH" u2013 to -
            #try:
            #    res = str(x.encode('iso-8859-1'))
            #except UnicodeEncodeError:
            #    tr={0x2013:0x2d}
            #    res = str(x.translate(tr).encode('iso-8859-1'))
        return res

    def action(self,table,action,columns=None,where=None):
        ############### GET #################
        if action == 'GET' or action == 'GET3':
            self.columns = ''
            if columns:
                self.a = 0
                for self.col in columns:
                    if self.a == 0:
                        self.columns = DB().dbstr(self.col)
                        self.order = DB().dbstr(self.col)
                    else:
                        self.columns = DB().dbstr(self.columns) + ',' + DB().dbstr(self.col)
                    self.a = self.a + 1
            else:
                self.columns = '*'
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
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ' ORDER BY ' + self.order +';'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' ORDER BY ' + self.order +';'
            if Debug: print 'sql:',self.sql
           # self.execute = DB().CursorExecute(self.sql)
           # if Debug: print 'executeOutput:',self.execute
           # return self.execute
            self.execute,errno, why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            if action == 'GET3':
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
                return self.execute,errno,str(why)+' SQL: ' + self.sql
            else:
                return self.execute

        ############### GET5 #################
        if action == 'GET5':
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
                for self.w in where:
                    if self.a == 0:             #First argument
                        self.where = str(self.w)
                        self.a = 1              #Flag that first argument is passed
                    else:
                        self.where += ' ' + str(self.w)
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' WHERE ' + self.where + ' ORDER BY ' + self.order +';'
            else:
                self.sql = 'SELECT ' + self.columns + ' FROM ' + table + ' ORDER BY ' + self.order +';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            return self.execute,errno,str(why)+' SQL: ' + self.sql

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
            return self.execute
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
            return self.execute
        ############### UPDATE/INSERT #################
        if action == 'UPD' or action == 'INS':
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
                        self.columns = DB().dbstr(self.columns) + '="' + DB().dbstr(self.col) + '"'
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
                if action == 'INS': self.sql = 'INSERT INTO ' + table + ' SET ' + self.columns + ';'
            if Debug: print 'sql:',self.sql
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            return self.execute,errno,str(why)+' SQL: ' + self.sql
            #return self.execute,errno,why

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
            self.execute,errno,why = DB().CursorExecute(self.sql)
            if Debug: print 'executeOutput:',self.execute
            return self.execute
            
    ###############################################
    def CursorExecute(self,sql):
        try:
            self.db=MySQLdb.connect(user=DBuser,passwd=DBpasswd,db=DBname)
            self.cursor = self.db.cursor()
            self.cursor.execute(sql)
        except (MySQLdb.OperationalError), (why):
            return '',4,why
        except (MySQLdb.ProgrammingError), (why):
            return '',3,why
        except (MySQLdb.Warning), (why):
            return self.cursor.fetchall(),5,why
        else:
            return self.cursor.fetchall(),0,''

###############################################
def escape_string(inputstring):
    inputstring = DB().dbstr(inputstring)
    outputstring = MySQLdb.escape_string(inputstring)
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
#print DB().action('archtape','GET',('t_id','status'),('t_id','GSU001'))
#print DB().action('archtape','GET2',('t_id','status'),('id',)
#t_id='FB1002'
#StorageTable='storage'
#print int(DB().action('storage','GETlast',('contentLocationValue',),('storageMediumID','=','"'+t_id+'"'))[0][0]) + 1
#print int(DB().action(StorageTable,'GETlast',('contentLocationValue',),('storageMediumID','=','"'+t_id+'"'))[0][0]) + 1

