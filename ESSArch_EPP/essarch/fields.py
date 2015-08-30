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

###########################################################################
#
# Custom fields
#
from django.db.models import fields
#from south.modelsinspector import add_introspection_rules
from django.core import exceptions

class BigAutoField(fields.AutoField):

    def db_type(self, connection):
        engine = connection.settings_dict['ENGINE']
        if 'mysql' in engine:
            return "bigint AUTO_INCREMENT"
        elif 'oracle' in engine:
            return "NUMBER(19)"
        elif 'postgres' in engine:
            return "bigserial"
        else:
            raise Exception('NotImplemented')

    def get_related_db_type(self, connection):
        return fields.BigIntegerField().db_type(connection)

    def get_internal_type(self):
        return "BigAutoField"

    def to_python(self, value):
        if value is None:
            return value
        try:
            return long(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                _("This value must be a long integer."))

#add_introspection_rules([], ["^essarch\.fields\.BigAutoField"])