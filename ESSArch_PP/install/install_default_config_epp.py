# -*- coding: UTF-8 -*-
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

import django
django.setup()

from django.contrib.auth.models import User, Group, Permission

from ESSArch_Core.configuration.models import ArchivePolicy, EventType, Parameter, Path
from ESSArch_Core.storage.models import (
    DISK,

    StorageMethod,
    StorageMethodTargetRelation,
    StorageTarget,
)


def installDefaultConfiguration():
    print "\nInstalling parameters..."
    installDefaultParameters()

    print "Installing users, groups and permissions..."
    installDefaultUsers()

    print "\nInstalling paths..."
    installDefaultPaths()

    print "\nInstalling event types..."
    installDefaultEventTypes()

    print "\nInstalling archive policies..."
    installDefaultArchivePolicies()

    print "\nInstalling storage methods..."
    installDefaultStorageMethods()

    print "\nInstalling storage targets..."
    installDefaultStorageTargets()

    print "\nInstalling storage method target relations..."
    installDefaultStorageMethodTargetRelations()

    return 0


def installDefaultParameters():
    site_name = 'Site-X'

    dct = {
        'site_name': site_name,
        'medium_location': 'Media_%s' % site_name,
    }

    for key in dct:
        print '-> %s: %s' % (key, dct[key])
        Parameter.objects.get_or_create(entity=key, value=dct[key])

    return 0


def installDefaultUsers():
    user_system, created = User.objects.get_or_create(
        username='system', email='system@essolutions.se',
        is_staff=True, is_superuser=True
    )
    if created:
        user_system.set_password('system')
        user_system.save()

    user_user, created = User.objects.get_or_create(
        username='user', email='usr1@essolutions.se'
    )
    if created:
        user_user.set_password('user')
        user_user.save()

    user_admin, created = User.objects.get_or_create(
        username='admin', email='admin@essolutions.se',
        is_staff=True
    )
    if created:
        user_admin.set_password('admin')
        user_admin.save()

    user_sysadmin, created = User.objects.get_or_create(
        username='sysadmin', email='sysadmin@essolutions.se',
        is_staff=True, is_superuser=True
    )
    if created:
        user_sysadmin.set_password('sysadmin')
        user_sysadmin.save()

    group_user, _ = Group.objects.get_or_create(name='user')
    group_admin, _ = Group.objects.get_or_create(name='admin')
    group_sysadmin, _ = Group.objects.get_or_create(name='sysadmin')

    can_add_ip_event = Permission.objects.get(codename='add_eventip')
    can_change_ip_event = Permission.objects.get(codename='change_eventip')
    can_delete_ip_event = Permission.objects.get(codename='delete_eventip')

    group_user.permissions.add(can_add_ip_event, can_change_ip_event, can_delete_ip_event)

    permission_list = [
        'receive', 'preserve', 'view', 'view_tar', 'edit_as_new', 'diff-check',
        'query',
    ]

    permissions = Permission.objects.filter(
        codename__in=permission_list, content_type__app_label='ip',
        content_type__model='informationpackage',
    )

    for p in permissions:
        group_user.permissions.add(p)
        group_admin.permissions.add(p)

    group_user.user_set.add(user_user)
    group_admin.user_set.add(user_admin)
    group_sysadmin.user_set.add(user_sysadmin)

    return 0


def installDefaultPaths():
    dct = {
        'path_mimetypes_definitionfile': '/ESSArch/config/mime.types',
        'reception': '/ESSArch/data/gate/reception',
        'ingest': '/ESSArch/data/epp/ingest',
        'cache': '/ESSArch/data/epp/cache',
        'access': '/ESSArch/data/epp/access',
        'disseminations': '/ESSArch/data/epp/disseminations',
        'orders': '/ESSArch/data/epp/orders',
        'verify': '/ESSArch/verify',
    }

    for key in dct:
        print '-> %s: %s' % (key, dct[key])
        Path.objects.get_or_create(entity=key, value=dct[key])

    return 0


def installDefaultEventTypes():
    dct = {
        'Delivery received': '30100',
        'Delivery checked': '30200',
        'Validate file format': '30260',
        'Validate XML file': '30261',
        'Validate logical representation against physical representation': '30262',
        'Validate checksum': '30263',
    }

    for key in dct:
        print '-> %s: %s' % (key, dct[key])
        EventType.objects.get_or_create(eventType=dct[key], eventDetail=key)

    return 0


def installDefaultArchivePolicies():
    cache = Path.objects.get(entity='cache')
    ingest = Path.objects.get(entity='ingest')

    ArchivePolicy.objects.update_or_create(
        policy_name='default',
        defaults={
            'cache_storage': cache, 'ingest_path': ingest,
            'receive_extract_sip': True
        }
    )

    return 0


def installDefaultStorageMethods():
    StorageMethod.objects.get_or_create(
        name='Default Storage Method 1',
        archive_policy=ArchivePolicy.objects.get(policy_name='default'),
        status=True,
        type=DISK,
    )

    return 0


def installDefaultStorageTargets():
    StorageTarget.objects.get_or_create(
        name='Default Storage Target 1',
        status=True,
        type=DISK,
        target=u'/ESSArch/data/store/disk1',
    )

    return 0


def installDefaultStorageMethodTargetRelations():
    StorageMethodTargetRelation.objects.get_or_create(
        name='Default Storage Method Target Relation 1',
        status=True,
        storage_method=StorageMethod.objects.get(name='Default Storage Method 1'),
        storage_target=StorageTarget.objects.get(name='Default Storage Target 1'),
    )

    return 0


if __name__ == '__main__':
    installDefaultConfiguration()
