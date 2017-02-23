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
from ESSArch_Core.configuration.models import EventType, Path


def installDefaultConfiguration():
    print "Installing users, groups and permissions..."
    installDefaultUsers()

    return 0


def installDefaultUsers():
    user_user, _ = User.objects.get_or_create(
        username='user', email='usr1@essolutions.se'
    )
    user_user.set_password('user')
    user_user.save()

    user_admin, _ = User.objects.get_or_create(
        username='admin', email='admin@essolutions.se',
        is_staff=True
    )
    user_admin.set_password('admin')
    user_admin.save()

    user_sysadmin, _ = User.objects.get_or_create(
        username='sysadmin', email='sysadmin@essolutions.se',
        is_staff=True, is_superuser=True
    )
    user_sysadmin.set_password('sysadmin')
    user_sysadmin.save()

    group_user, _ = Group.objects.get_or_create(name='user')
    group_admin, _ = Group.objects.get_or_create(name='admin')
    group_sysadmin, _ = Group.objects.get_or_create(name='sysadmin')

    can_add_ip_event = Permission.objects.get(codename='add_eventip')
    can_change_ip_event = Permission.objects.get(codename='change_eventip')
    can_delete_ip_event = Permission.objects.get(codename='delete_eventip')

    group_user.permissions.add(can_add_ip_event, can_change_ip_event, can_delete_ip_event)

    group_user.user_set.add(user_user)
    group_admin.user_set.add(user_admin)
    group_sysadmin.user_set.add(user_sysadmin)

    return 0


if __name__ == '__main__':
    installDefaultConfiguration()
