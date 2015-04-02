#!/usr/bin/env /ESSArch/pd/python/bin/python 
# -*- coding: UTF-8 -*-
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

import sqlite3
import os
import sys
import tempfile
import random
#import logging

from threading import Thread
from sys import version_info

# Minimum version required version 2.5;
# python 2.5 has a syntax which is already incompatible
# but newer pythons in  2 series ara easily forward compatible
_major_version=version_info[0]
if _major_version<3: # py <= 2.x
    if version_info[1]<5: # py <= 2.4
        raise ImportError("sqlitedict requires python 2.5 or higher (python 3.3 or higher supported)")

try:
    from cPickle import dumps, loads, HIGHEST_PROTOCOL as PICKLE_PROTOCOL
except ImportError:
    from pickle import dumps, loads, HIGHEST_PROTOCOL as PICKLE_PROTOCOL

# some Python 3 vs 2 imports
#try:
#    from collections import UserList as ListClass
#except ImportError:
#    from UserList import UserList as ListClass

try:
    from queue import Queue
except ImportError:
    from Queue import Queue

#logger = logging.getLogger(__name__)

#def open(*args, **kwargs):
#    """See documentation of the SqliteList class."""
#    return SqliteList(*args, **kwargs)


def encode(obj):
    """Serialize an object using pickle to a binary format accepted by SQLite."""
    return sqlite3.Binary(dumps(obj, protocol=PICKLE_PROTOCOL))


def decode(obj):
    """Deserialize objects retrieved from SQLite."""
    return loads(bytes(obj))


#class SqliteList(ListClass):
class SqliteList(object):
    def __init__(self, filename=None, tablename='unnamed', flag='c',
                 autocommit=False, journal_mode="DELETE"):
        """
        Initialize a thread-safe sqlite-backed list. The list will
        be a table `tablename` in database file `filename`. A single file (=database)
        may contain multiple tables.

        If no `filename` is given, a random file in temp will be used (and deleted
        from temp once the list is closed/deleted).

        If you enable `autocommit`, changes will be committed after each operation
        (more inefficient but safer). Otherwise, changes are committed on `self.commit()`,
        `self.clear()` and `self.close()`.

        Set `journal_mode` to 'OFF' if you're experiencing sqlite I/O problems
        or if you need performance and don't care about crash-consistency.

        The `flag` parameter:
          'c': default mode, open for read/write, creating the db/table if necessary.
          'w': open for r/w, but drop `tablename` contents first (start with empty table)
          'n': create a new database (erasing any existing tables, not just `tablename`!).

        """
        self.in_temp = filename is None
        if self.in_temp:
            randpart = hex(random.randint(0, 0xffffff))[2:]
            filename = os.path.join(tempfile.gettempdir(), 'sqllist' + randpart)
        if flag == 'n':
            if os.path.exists(filename):
                os.remove(filename)

        dirname = os.path.dirname(filename)
        if dirname:
            if not os.path.exists(dirname):
                raise RuntimeError('Error! The directory does not exist, %s' % dirname)

        self.filename = filename
        self.tablename = tablename

#        logger.info("opening Sqlite table %r in %s" % (tablename, filename))
        MAKE_TABLE = 'CREATE TABLE IF NOT EXISTS %s (key INTEGER PRIMARY KEY, value BLOB)' % self.tablename
        self.conn = SqliteMultithread(filename, autocommit=autocommit, journal_mode=journal_mode)
        self.conn.execute(MAKE_TABLE)
        self.conn.commit()
        if flag == 'w':
            self.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def __str__(self):
        return "SqliteList(%s)" % (self.conn.filename)

    def __repr__(self):
        return str(self) # no need of something complex

    def __len__(self):
        # `select count (*)` is super slow in sqlite (does a linear scan!!)
        # As a result, len() is very slow too once the table size grows beyond trivial.
        # We could keep the total count of rows ourselves, by means of triggers,
        # but that seems too complicated and would slow down normal operation
        # (insert/delete etc).
        GET_LEN = 'SELECT COUNT(*) FROM %s' % self.tablename
        rows = self.conn.select_one(GET_LEN)[0]
        return rows if rows is not None else 0

    def __bool__(self):
        # No elements is False, otherwise True
        GET_MAX = 'SELECT MAX(ROWID) FROM %s' % self.tablename
        m = self.conn.select_one(GET_MAX)[0]
        # Explicit better than implicit and bla bla
        return True if m is not None else False
    
    def select_one(self, req, arg=tuple()):
        """Return only the first row of the SELECT, or None if there are no matching rows."""
        try:
            return next(iter(self.cursor.execute(req, arg)))
        except StopIteration:
            return None

    def keys(self):
        GET_KEYS = 'SELECT key FROM %s ORDER BY rowid' % self.tablename
        return [key[0] for key in self.conn.select(GET_KEYS)]

    def iterkeys(self):
        GET_KEYS = 'SELECT key FROM %s ORDER BY rowid' % self.tablename
        for key in self.conn.select(GET_KEYS):
            yield key[0]

    def values(self):
        GET_VALUES = 'SELECT value FROM %s ORDER BY rowid' % self.tablename
        return  [decode(value[0]) for value in self.conn.select(GET_VALUES)]

    def itervalues(self):
        GET_VALUES = 'SELECT value FROM %s ORDER BY rowid' % self.tablename
        for value in self.conn.select(GET_VALUES):
            yield decode(value[0])

    def items(self):
        GET_ITEMS = 'SELECT key, value FROM %s ORDER BY rowid' % self.tablename
        return [(key,decode(value)) for key,value in self.conn.select(GET_ITEMS)]

    def iteritems(self):
        GET_ITEMS = 'SELECT key, value FROM %s ORDER BY rowid' % self.tablename
        for key,value in self.conn.select(GET_ITEMS):
            yield (key,decode(value))

    def __contains__(self, key):
        HAS_ITEM = 'SELECT 1 FROM %s WHERE key = ?' % self.tablename
        return self.conn.select_one(HAS_ITEM, (key,)) is not None

    def __getitem__(self, key):
        GET_ITEM = 'SELECT value FROM %s WHERE key = ?' % self.tablename
        item = self.conn.select_one(GET_ITEM, (key,))
        if item is None:
            raise KeyError(key)
        return decode(item[0])

    def __setitem__(self, key, value):
        ADD_ITEM = 'REPLACE INTO %s (key, value) VALUES (?,?)' % self.tablename
        self.conn.execute(ADD_ITEM, (key, encode(value)))

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        DEL_ITEM = 'DELETE FROM %s WHERE key = ?' % self.tablename
        self.conn.execute(DEL_ITEM, (key,))

    def append(self, x=None):
        UPDATE_ITEMS = 'INSERT INTO %s (value) VALUES (?)' % self.tablename
        self.conn.execute(UPDATE_ITEMS, (encode(x),))
        if self.conn.autocommit:
            self.conn.commit()

    def extend(self, l=(),):
        items = [(encode(v),) for v in l]
        del l
        UPDATE_ITEMS = 'INSERT INTO %s (value) VALUES (?)' % self.tablename
        self.conn.executemany(UPDATE_ITEMS, items)
        if self.conn.autocommit:
            self.conn.commit()

    def __iter__(self):
        return self.itervalues()

    def clear(self):
        CLEAR_ALL = 'DELETE FROM %s;' % self.tablename # avoid VACUUM, as it gives "OperationalError: database schema has changed"
        self.conn.commit()
        self.conn.execute(CLEAR_ALL)
        self.conn.commit()

    def commit(self):
        if self.conn is not None:
            self.conn.commit()
    sync = commit

    def close(self):
#        logger.debug("closing %s" % self)
        if self.conn is not None:
            if self.conn.autocommit:
                self.conn.commit()
            self.conn.close()
            self.conn = None
        if self.in_temp:
            try:
                os.remove(self.filename)
            except:
                pass

    def terminate(self):
        """Delete the underlying database file. Use with care."""
        self.close()

        if self.filename == ':memory:':
            return

#        logger.info("deleting %s" % self.filename)
        try:
            os.remove(self.filename)
        except IOError:
            _, e, _ = sys.exc_info() # python 2.5: "Exception as e"
#            logger.warning("failed to delete %s: %s" % (self.filename, str(e)))

    def __del__(self):
        # like close(), but assume globals are gone by now (such as the logger)
        try:
            if self.conn is not None:
                if self.conn.autocommit:
                    self.conn.commit()
                self.conn.close()
                self.conn = None
            if self.in_temp:
                os.remove(self.filename)
        except:
            pass

# Adding extra methods for python 2 compatibility (at import time)
if _major_version == 2:
    #setattr(SqliteDict,"iterkeys",lambda self: self.keys())
    #setattr(SqliteDict,"itervalues",lambda self: self.values())
    #setattr(SqliteDict,"iteritems",lambda self: self.items())
    SqliteList.__nonzero__ = SqliteList.__bool__#SqliteDict.__bool__
    del SqliteList.__bool__ #not needed and confusing
#endclass SqliteDict

class SqliteMultithread(Thread):
    """
    Wrap sqlite connection in a way that allows concurrent requests from multiple threads.

    This is done by internally queueing the requests and processing them sequentially
    in a separate thread (in the same order they arrived).

    """
    def __init__(self, filename, autocommit, journal_mode):
        super(SqliteMultithread, self).__init__()
        self.filename = filename
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.reqs = Queue() # use request queue of unlimited size
        self.setDaemon(True) # python2.5-compatible
        self.start()

    def run(self):
        if self.autocommit:
            conn = sqlite3.connect(self.filename, isolation_level=None, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.filename, check_same_thread=False)
        conn.execute('PRAGMA journal_mode = %s' % self.journal_mode)
        conn.text_factory = str
        cursor = conn.cursor()
        cursor.execute('PRAGMA synchronous=OFF')
        while True:
            sql, arg, res, req = self.reqs.get()
            if req == '--close--':
                break
            elif req == '--commit--':
                conn.commit()
            elif req == '--executemany--':
                cursor.executemany(sql, arg)
                #if res:
                #   for rec in cursor:
                #        res.put(rec)
                #    res.put('--no more--')
                if self.autocommit:
                    conn.commit()
                del sql
                del arg
            else:
                cursor.execute(sql, arg)
                if res:
                    for rec in cursor:
                        res.put(rec)
                    res.put('--no more--')
                if self.autocommit:
                    conn.commit()
            self.reqs.task_done()
        conn.close()
        del self.reqs

    def execute(self, sql='', arg=None, res=None, req=None):
        """
        `execute` calls are non-blocking: just queue up the request and return immediately.

        """
        self.reqs.put((sql, arg or tuple(), res, req))

    def executemany(self, sql, items):
        self.execute(sql, items, req='--executemany--')
#        for item in items:
#            self.execute(req, item)

    def select(self, sql, arg=None):
        """
        Unlike sqlite's native select, this select doesn't handle iteration efficiently.

        The result of `select` starts filling up with values as soon as the
        request is dequeued, and although you can iterate over the result normally
        (`for res in self.select(): ...`), the entire result will be in memory.

        """
        res = Queue() # results of the select will appear as items in this queue
        self.execute(sql, arg, res)
        while True:
            rec = res.get()
            if rec == '--no more--':
                break
            yield rec

    def select_one(self, req, arg=None):
        """Return only the first row of the SELECT, or None if there are no matching rows."""
        try:
            return next(iter(self.select(req, arg)))
        except StopIteration:
            return None

    def commit(self):
        self.execute(req='--commit--')

    def close(self):
        self.execute(req='--close--')
        self.join()
#endclass SqliteMultithread
