"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

"""
Django settings for EPP project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'x3lzf9b+nq_0nnu(&q3ukdo^97gpp2(x4yonr+5x@m9m9d8ftg'
SESSION_COOKIE_NAME = 'epp'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Rest framework
REST_FRAMEWORK = {
    'DEFAULT_METADATA_CLASS': 'ESSArch_Core.metadata.CustomMetadata',
    'DEFAULT_PAGINATION_CLASS': 'proxy_pagination.ProxyPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PERMISSION_CLASSES': (
      'rest_framework.permissions.IsAuthenticated',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

PROXY_PAGINATION_PARAM = 'pager'
PROXY_PAGINATION_DEFAULT = 'ESSArch_Core.pagination.LinkHeaderPagination'
PROXY_PAGINATION_MAPPING = {'none': 'ESSArch_Core.pagination.NoPagination'}

# Application definition

INSTALLED_APPS = [
    'allauth',
    'allauth.account',
    'channels',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.sites',
    'django_filters',
    'nested_inline',
    'rest_auth',
    'rest_auth.registration',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'mptt',
    'frontend',
    'ESSArch_Core.auth',
    'ESSArch_Core.config',
    'ESSArch_Core.configuration',
    'ESSArch_Core.docs',
    'ESSArch_Core.ip',
    'ESSArch_Core.maintenance',
    'ESSArch_Core.profiles',
    'ESSArch_Core.essxml.Generator',
    'ESSArch_Core.essxml.ProfileMaker',
    'ESSArch_Core.fixity',
    'ESSArch_Core.storage',
    'ESSArch_Core.tags',
    'ESSArch_Core.WorkflowEngine',
    'configuration',
    'storage',
    'guardian',
    'groups_manager',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

GROUPS_MANAGER = {
    'AUTH_MODELS_SYNC': True,
    'PERMISSIONS': {
        'owner': [],
        'group': [],
        'groups_upstream': [],
        'groups_downstream': [],
        'groups_siblings': [],
    },
    'GROUP_NAME_PREFIX': '',
    'GROUP_NAME_SUFFIX': '',
    'USER_USERNAME_PREFIX': '',
    'USER_USERNAME_SUFFIX': '',
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "ROUTING": "ESSArch_Core.routing.channel_routing",
        "CONFIG": {
            "hosts": ["redis://localhost/3"],
        },
    },
}

SITE_ID = 1

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ORIGIN_ALLOW_ALL = True
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'epp',                    # Or path to database file if using sqlite3.
        'USER': 'arkiv',                      # Not used with sqlite3.
        'PASSWORD': 'password',               # Not used with sqlite3.
        'HOST': '',                           # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                           # Set to empty string for default. Not used with sqlite3.
    }
}

# Cache
CACHES = {
    'default': {
        'TIMEOUT': None,
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

ELASTICSEARCH_DSL={
    'default': {
        'hosts': 'localhost:9200'
    },
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'core': {
            'level': 'DEBUG',
            'class': 'ESSArch_Core.log.dbhandler.DBHandler',
            'application': 'ESSArch Preservation Platform',
            'agent_role': 'Archivist',
        }
    },
    'loggers': {
        'essarch': {
            'handlers': ['core'],
            'level': 'DEBUG',
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Rest auth
REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'ESSArch_Core.auth.serializers.UserLoggedInSerializer'
}

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# File elements in different metadata standards

FILE_ELEMENTS = {
    "file": {
        "path": "FLocat@href",
        "pathprefix": "file:///",
        "checksum": "@CHECKSUM",
        "checksumtype": "@CHECKSUMTYPE",
    },
    "mdRef": {
        "path": "@href",
        "pathprefix": "file:///",
        "checksum": "@CHECKSUM",
        "checksumtype": "@CHECKSUMTYPE",
    },
    "object": {
        "path": "storage/contentLocation/contentLocationValue",
        "pathprefix": "file:///",
        "checksum": "objectCharacteristics/fixity/messageDigest",
        "checksumtype": "objectCharacteristics/fixity/messageDigestAlgorithm",
        "format": "objectCharacteristics/format/formatDesignation/formatName",
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Stockholm'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# Documentation
DOCS_ROOT = os.path.join(BASE_DIR, 'docs/_build/html')

# Add epp vhost to rabbitmq:
# rabbitmqctl add_user guest guest
# rabbitmqctl add_vhost epp
# rabbitmqctl set_permissions -p epp guest ".*" ".*" ".*"

# Celery settings
BROKER_URL = 'amqp://guest:guest@localhost:5672/epp'
CELERY_IMPORTS = ("workflow.tasks", "ESSArch_Core.WorkflowEngine.tests.tasks",)
CELERY_RESULT_BACKEND = 'redis://'
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
   'PollAccessQueue-every-10-seconds': {
        'task': 'workflow.tasks.PollAccessQueue',
        'schedule': timedelta(seconds=10),
    },
    'PollIOQueue-every-10-seconds': {
        'task': 'workflow.tasks.PollIOQueue',
        'schedule': timedelta(seconds=10),
    },
    'PollRobotQueue-queue-every-10-seconds': {
        'task': 'workflow.tasks.PollRobotQueue',
        'schedule': timedelta(seconds=10),
    },
    'UnmountIdleDrives-queue-every-10-seconds': {
        'task': 'workflow.tasks.UnmountIdleDrives',
        'schedule': timedelta(seconds=10),
    },
    'PollAppraisalJobs-every-10-seconds': {
        'task': 'workflow.tasks.PollAppraisalJobs',
        'schedule': timedelta(seconds=10),
    },
    'ScheduleAppraisalJobs-every-10-seconds': {
        'task': 'workflow.tasks.ScheduleAppraisalJobs',
        'schedule': timedelta(seconds=10),
    },
    'PollConversionJobs-every-10-seconds': {
        'task': 'workflow.tasks.PollConversionJobs',
        'schedule': timedelta(seconds=10),
    },
    'ScheduleConversionJobs-every-10-seconds': {
        'task': 'workflow.tasks.ScheduleConversionJobs',
        'schedule': timedelta(seconds=10),
    },
}

# Rest auth settings
OLD_PASSWORD_FIELD_ENABLED = True

try:
    from local_epp_settings import *
except ImportError, exp:
    pass
