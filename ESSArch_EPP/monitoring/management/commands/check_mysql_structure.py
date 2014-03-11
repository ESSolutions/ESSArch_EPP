"""
This command reads through the Django model definitions and compares each field
with the equivalent column in MySQL, printing any differences found.

It is intended that this be run when you have to update a database, as opposed to
recreating it using syncdb. Having delivered new code it can be run to see what needs
to change. Having updated the database structure it can be run again to confirm that
that matches the models.

It prints out any differences; Output structure: Model.Field v Table.Column: Difference

Usage
-----

   python manage.py check_mysql_structure [database] [django_app] [model]

 * No parameters are required.
 * The first parameter is the name of a database. This does not have to be the database
   in Django but it does need to use the same Host, Username and Password.
 * The second parameter is the name of a Django application. If present then only
   models/tables in that application are checked.
 * The third parameter is the name of a Django model. If present then only that model
   is checked.
"""
from django.contrib.contenttypes.models import ContentType
from django.db import connection as db_connection
from django.db.models.fields import AutoField, BigIntegerField, BooleanField, CharField,\
    CommaSeparatedIntegerField, DateField, DateTimeField, DecimalField,\
    EmailField, FilePathField, FloatField, IPAddressField, IntegerField,\
    NullBooleanField, PositiveIntegerField, PositiveSmallIntegerField,\
    SlugField, SmallIntegerField, TextField, TimeField, URLField
from django.db.models.fields.files import FileField, ImageField
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.core.management.base import BaseCommand
from django.conf import settings
import MySQLdb

FIELD_TYPES_CHECKED = [
    AutoField, BigIntegerField, BooleanField, CharField,
    CommaSeparatedIntegerField, DateField, DateTimeField,
    DecimalField, EmailField, FileField, FilePathField,
    FloatField, ForeignKey, IPAddressField, ImageField,
    IntegerField, ManyToManyField, NullBooleanField,
    OneToOneField, PositiveIntegerField, PositiveSmallIntegerField,
    SlugField, SmallIntegerField, TextField, TimeField, URLField
]

# MySQL Column definitions which are not exact matches for equivalent Django Field.db_type():
COLUMN_DEFINITIONS = {
    'bool': 'tinyint(1)',                               # BooleanField
    'bigint': 'bigint(20)',                             # BigIntegerField
    'double precision': 'double',                       # FloatField
    'integer': 'int(11)',                               # IntegerField
    'integer AUTO_INCREMENT': 'int(11)',                # AutoField
    'integer UNSIGNED': 'int(10) unsigned',             # PositiveIntegerField
    'smallint UNSIGNED': 'smallint(5) unsigned',        # PositiveSmallIntegerField
    'smallint': 'smallint(6)',                          # SmallIntegerField
}


class Command(BaseCommand):
    args = 'database_name app_name model_name'
    help = "Compare attributes of fields in models to those of equivalent columns on mysql tables."

    def handle(self, *args, **options):
        """
        Read through the Content Types, get the model definitions and check that each field is
        defined correctly in the database.
        """
        database_name = args[0] if len(args) > 0 else settings.DATABASES['default']['NAME']
        app_label = args[1].lower() if len(args) > 1 else None
        model_name = args[2].lower() if len(args) > 2 else None
        if model_name:
            try:
                content_types = [ContentType.objects.get(app_label=app_label, model=model_name)]
            except ContentType.DoesNotExist:
                print 'No ContentType found for app.model_name "%s.%s".' % (app_label, model_name)
                return
        elif app_label:
            content_types = ContentType.objects.filter(app_label=app_label)
        else:
            content_types = ContentType.objects.all()
        if not content_types:
            print 'No ContentType found' + ' for app "%s"' % (app_label) if app_label else ''

        try:
            connection = MySQLdb.connect(
                db=database_name,
                user=settings.DATABASES['default']['USER'],
                passwd=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                use_unicode=False,
                charset='utf8')
            cursor = connection.cursor()
        except Exception, e:
            print 'Could not connect to database "%s". %s.' % (database_name, e)
            return

        table_count = 0
        field_count = 0
        difference_count = 0
        for content_type in content_types:
            model_class = content_type.model_class()
            if not model_class:
                print 'No model_class found for "%s".' % (content_type)
                continue
            model_name = model_class._meta.object_name
            table_name = model_class._meta.db_table
            sql = "DESCRIBE %s" % table_name
            try:
                cursor.execute(sql)
                rows = cursor.fetchall()
            except Exception, e:
                print 'Could not DESCRIBE table "%s" on database "%s" %s.' % (table_name, database_name, e)
                continue
            table_count += 1
            # Sample rows returned from DESCRIBE MySQL Command:
            # +----------+--------------+------+-----+---------+----------------+
            # | Field    | Type         | Null | Key | Default | Extra          |
            # +----------+--------------+------+-----+---------+----------------+
            # | id       | int(11)      | NO   | PRI | NULL    | auto_increment |
            # | level    | varchar(10)  | NO   |     | NULL    |                |
            # | msg      | varchar(600) | YES  |     | NULL    |                |
            # | datetime | datetime     | NO   |     | NULL    |                |
            # +----------+--------------+------+-----+---------+----------------+
            columns = {
                row[0]: {
                    'type': row[1],
                    'null': row[2] == 'YES',
                    'primary_key': row[3] == 'PRI',
                    'index': row[3] != '',
                    'default': row[4],
                    'extra': row[5],
                } for row in rows
            }
            for field in model_class._meta.fields:
                field_type = type(field)
                field_name = field.name
                if field.db_column:
                    column_name = field.db_column
                elif field_type == ForeignKey or field_type == OneToOneField:
                    column_name = field_name + '_id'
                else:
                    column_name = field_name
                msg_pfx = '%s.%s v %s.%s:' % (model_name, field_name, table_name, column_name)
                if field_type not in FIELD_TYPES_CHECKED:
                    print '%s Field type "%s" not validated.' % (msg_pfx, field_type)
                    continue
                field_count += 1
                if column_name in columns:
                    column_attr = columns[column_name]
                    field_db_type = field.db_type(db_connection)
                    if field_type == DecimalField:
                        field_db_type = 'decimal(%s,%s)' % (field.max_digits, field.decimal_places)
                    elif field_db_type in COLUMN_DEFINITIONS:
                        if COLUMN_DEFINITIONS[field_db_type] != column_attr['type']:
                            print '%s Expected column type "%s"; Found "%s".' % (msg_pfx, COLUMN_DEFINITIONS[field_type], column_attr['type'])
                            difference_count += 1
                    elif field_db_type != column_attr['type']:
                        print '%s Expected column type "%s"; Found "%s".' % (msg_pfx, field_db_type, column_attr['type'])
                        difference_count += 1
                    if field.null != column_attr['null']:
                        print '%s On model null is "%s" but on table null is "%s".' % (msg_pfx, field.null, column_attr['null'])
                        difference_count += 1
                    if field.primary_key != column_attr['primary_key']:
                        print '%s On model primary_key is "%s" but on table primary_key is "%s".' % (msg_pfx, field.primary_key, column_attr['field_name'])
                        difference_count += 1
                    if field.db_index and not column_attr['index']:
                        print '%s Should have been an index key.' % (msg_pfx)
                        difference_count += 1
                    if field_type == AutoField and column_attr['extra'] != 'auto_increment':
                        print '%s Expected "auto_increment" attribute on column.' % (msg_pfx)
                        difference_count += 1
                else:
                    print '%s Column missing from table.' % (msg_pfx)
                    difference_count += 1
        print 'Checked %s columns on %s tables, %s differences found.' % (field_count, table_count, difference_count)
"""

Table containing all types of fields. Add to a models.py and run syncdb to test.

 class FieldsTestModel(models.Model):
    AutoField = models.AutoField(primary_key=True)
    BooleanField = models.BooleanField()
    CharField = models.CharField(max_length=10)
    DateField = models.DateField()
    DateTimeField = models.DateTimeField()
    DecimalField = models.DecimalField(max_digits=4, decimal_places=2)
    EmailField = models.EmailField()
    FloatField = models.FloatField()
    IntegerField = models.IntegerField()
    NullBooleanField = models.NullBooleanField()
    PositiveIntegerField = models.PositiveIntegerField()
    PositiveSmallIntegerField = models.PositiveSmallIntegerField()
    TextField = models.TextField()
    TimeField = models.TimeField()
    CommaSeparatedIntegerField = models.CommaSeparatedIntegerField(max_length=10)
    FilePathField = models.FilePathField()
    BigIntegerField = models.BigIntegerField()
    IPAddressField = models.IPAddressField()
    SlugField = models.SlugField()
    SmallIntegerField = models.SmallIntegerField()
    URLField = models.URLField()
    FileField = models.FileField(upload_to='/')
    ImageField = models.ImageField(upload_to='/')
    ForeignKey = models.ForeignKey('self', related_name='foreignkey')
    OneToOneField = models.OneToOneField('self', related_name='onetoone')
    #ManyToManyField = models.ManyToManyField('self', related_name='manytomany') Not equivalent to a db column
"""
