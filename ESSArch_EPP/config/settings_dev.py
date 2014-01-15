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

#############################################################################
# Settings for ESSArch Preservation Platform.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['*']

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        #'STORAGE_ENGINE': 'MyISAM',           # STORAGE_ENGINE for MySQL database tables, 'MyISAM' or 'INNODB'
        'NAME': 'essarch',                    # Or path to database file if using sqlite3.
        'USER': 'arkiv',                      # Not used with sqlite3.
        'PASSWORD': 'password',               # Not used with sqlite3.
        'HOST': '',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                           # Set to empty string for default. Not used with sqlite3.
        # This options for storage_engine have to be set for "south migrate" to work.
        'OPTIONS': {
           "init_command": "SET storage_engine=MyISAM",
        }
    }
}

# Email configuration
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
SERVER_EMAIL = 'ESSArch@localhost' # from
DEFAULT_FROM_EMAIL = 'ESSArch_Default@localhost'

# django-log-files-viewer
#LOG_FILES_DIR = '/ESSArch/log'
#LOG_FILES_RE = '(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s\[(?P<type>[A-Z]+)\]\s(?P<message>.+)'
#LOG_FILES_RE = '(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s(?P<type>[A-Z]+)\s(?P<message>.+)'

# ESS Django process
#LOG_FILES_NAME_1 = ['celery_worker1','controlarea','ESSArch_db','ESSArch','storageLogistics','storagemaintenance','Tools']
#LOG_FILES_RE_1 = '(?P<type>[A-Z]+)\s(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s(?P<module>[a-zA-Z]+)\s(?P<process>[0-9]+)\s(?P<thread>[0-9]+)\s(?P<message>.+)'

# ESS core process
#LOG_FILES_NAME_2 = ['AccessEngine','AIPChecksum','AIPCreator','AIPPurge','AIPValidate','AIPWriter','AIPWriter_2','db_sync_ais','ESSlogging','ESSpreingest',
 #                   'FTPServer','IOEngine_2','IOEngine','SIPReceiver','SIPRemove','SIPValidateAIS','SIPValidateApproval','SIPValidateFormat','TLD']
#LOG_FILES_RE_2 = '(?P<date>\d{2} [a-zA-Z]+ \d{4} \d{2}:\d{2}:\d{2})\s(?P<type>[\/\-\w]+)\s(?P<message>.+)'

#format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
    # Is a regex to parse your log file against. It completely depends of your Django logging settings.
    # And table column names (in a parsed logfile) depend from group names you provide in the regexp.
    # E.g. for Django logging server to parse with this regexp you need to have log, as in example
    # django_log_file_viewer/testdata/testing.log file.

    # to produce this log I've added this formatter to my website.
    
    #'formatters': {
    #    'verbose': {
    #        'format': '%(asctime)s [%(levelname)s] %(message)s'
    #    },
    #},

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Stockholm'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'sv-SE'
#LANGUAGE_CODE = 'no-nyn'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/ESSArch/app/test/media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/ESSArch/app/test/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #"/ESSArch/app/static",
    "/home/henrik/workspace/ESSArch_Django/static",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'olkgd-#9pvgs3pmuwpk4v@)17d$@bij0&t8e#7wybgitrv1r@)'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.locale.LocaleMiddleware',
    #'djangomako.middleware.MakoMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',

)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

ROOT_URLCONF = 'config.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #"/ESSArch/app/templates",
    "/home/henrik/workspace/ESSArch_Django/templates"
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'grappelli',
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    'south',
    'djcelery',
    'django_tables2',
    'djangojs',
    'eztables',
    'configuration',
    'storagelogistics',
    'essarch',
    'controlarea',
    'access',
    'ingest',
    'administration',
    'reports',
    'django-log-file-viewer',
)

import djcelery
djcelery.setup_loader()

BROKER_URL = 'amqp://guest:guest@localhost:5672/'
CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'

# Logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'log_file_request': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/ESSArch_request.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 5,
        },
        'log_file_db': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/ESSArch_db.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 5,
        },
        'log_file_essarch': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/ESSArch.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 5,
        },
        'log_file_controlarea': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/controlarea.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 5,
        },
        'log_file_storagemaintenance': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/storagemaintenance.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 1000,
        },
        'log_file_storagelogistics': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/storageLogistics.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 1000,
        },
        'log_file_administration': {
            'level': 'DEBUG',
            #'filters': ['require_debug_false'],
            'class' : 'logging.handlers.RotatingFileHandler',
            'formatter': 'verbose',
            'filename': '/ESSArch/log/administration.log',
            'maxBytes': 1024*1024*5, # 5MB
            'backupCount': 1000,
        },
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['null'],
            'propagate': True,
        },
        'django.request': {
            'level': 'ERROR',
            'handlers': ['log_file_request', 'mail_admins'],
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['log_file_db'],
            'propagate': True,
        },
        'essarch': {
            'level': 'INFO',
            'handlers': ['null'],
            'propagate': True,
        },
        'essarch.controlarea': {
            'level': 'INFO',
            'handlers': ['log_file_controlarea'],
            'propagate': True,
        },
        'essarch.storagemaintenance': {
            'level': 'INFO',
            'handlers': ['log_file_storagemaintenance'],
            'propagate': True,
        },
        'essarch.storagelogistics': {
            'level': 'INFO',
            'handlers': ['log_file_storagelogistics'],
            'propagate': True,
        },
        'essarch.administration': {
            'level': 'INFO',
            'handlers': ['log_file_administration'],
            'propagate': True,
        },
    },
}
