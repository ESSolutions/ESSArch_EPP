"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Tools for Producer (ETP)
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

import os
import shutil
import tempfile
import uuid

from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.test import TestCase
from django.urls import reverse

import mock

from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.configuration.models import ArchivePolicy, Path
from ESSArch_Core.ip.models import InformationPackage, Order, Workarea
from ESSArch_Core.profiles.models import Profile, ProfileSA, SubmissionAgreement
from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask
from ESSArch_Core.util import timestamp_to_datetime


class AccessTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.root = os.path.dirname(os.path.realpath(__file__))
        self.datadir = os.path.join(self.root, 'datadir')

        self.ip = InformationPackage.objects.create(object_path=self.datadir)
        self.url = reverse('informationpackage-detail', args=(str(self.ip.pk),))
        self.url = self.url + 'access/'

    @mock.patch('ip.views.ProcessStep.run')
    def test_no_valid_option_set(self, mock_step):
        res = self.client.post(self.url, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()

    @mock.patch('ip.views.ProcessStep.run')
    def test_no_valid_option_set_to_true(self, mock_step):
        res = self.client.post(self.url, {'tar': False}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()

    @mock.patch('ip.views.ProcessStep.run')
    def test_not_in_workarea(self, mock_step):
        res = self.client.post(self.url, {'tar': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mock_step.assert_called_once()

    @mock.patch('ip.views.ProcessStep.run')
    def test_already_in_workarea(self, mock_step):
        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.post(self.url, {'tar': True}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_step.assert_not_called()


class WorkareaViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.ip = InformationPackage.objects.create(generation=0)
        self.url = reverse('workarea-list')

        Path.objects.create(entity='ingest_workarea', value='ingest')
        Path.objects.create(entity='access_workarea', value='access')

    def test_empty(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_post(self):
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_invalid_workarea(self):
        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'non-existing-workarea'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ip_in_workarea_by_other_user(self):
        user2 = User.objects.create()
        Workarea.objects.create(user=user2, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_multiple_aips_one_in_other_users_workarea_with_filter(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)

        user2 = User.objects.create(username="admin2", password='admin')
        Workarea.objects.create(user=self.user, ip=aip, type=Workarea.ACCESS, read_only=False)
        Workarea.objects.create(user=user2, ip=aip2, type=Workarea.ACCESS, read_only=False)

        res = self.client.get(self.url, data={'view_type': 'aic', 'object_identifier_value': aip2.object_identifier_value})

        self.assertEqual(len(res.data), 0)

    def test_ip_in_workarea_by_current_user_ip_view_type(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        ip3 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=2)
        user2 = User.objects.create()
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'ip'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'ip'})
        self.assertEqual(len(res.data[0]['information_packages']), 1)

        Workarea.objects.create(user=user2, ip=ip3, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'ip'})
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_in_workarea_by_current_user_aic_view_type(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        ip3 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=2)
        user2 = User.objects.create()
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'aic'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'aic'})
        self.assertEqual(len(res.data[0]['information_packages']), 2)

        Workarea.objects.create(user=user2, ip=ip3, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'workarea': 'access', 'view_type': 'aic'})
        self.assertEqual(len(res.data[0]['information_packages']), 2)

    def test_ip_in_workarea_by_current_user_ip_view_type_first_generation_not_in_workarea(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'ip'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(ip2.pk))

    def test_ip_in_workarea_by_current_user_ip_view_type_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(label='bar', package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.label = 'foo'
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)
        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'ip', 'search': 'foo'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

    def test_ip_in_workarea_by_current_user_aic_view_type_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        ip2 = InformationPackage.objects.create(label='second', package_type=InformationPackage.AIP, aic=aic, generation=1)
        self.ip.aic = aic
        self.ip.label = 'first'
        self.ip.save()

        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)
        Workarea.objects.create(user=self.user, ip=ip2, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access', 'view_type': 'aic', 'search': 'first'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(self.ip.pk))

class WorkareaFilesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.datadir = tempfile.mkdtemp()
        Path.objects.create(entity='access', value=self.datadir)

        self.path = os.path.join(self.datadir, str(self.user.pk))
        os.mkdir(self.path)

        self.url = reverse('workarea-files-list')

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

    def test_no_type_parameter(self):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_type_parameter(self):
        res = self.client.get(self.url, {'type': 'invalidtype'})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_file(self):
        _, path = tempfile.mkstemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access'})

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(path), 'size': os.stat(path).st_size, 'modified': timestamp_to_datetime(os.stat(path).st_mtime)}])

    def test_list_file_content(self):
        _, path = tempfile.mkstemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_folder(self):
        path = tempfile.mkdtemp(dir=self.path)
        res = self.client.get(self.url, {'type': 'access'})

        self.assertEqual(res.data, [{'type': 'dir', 'name': os.path.basename(path), 'size': 0, 'modified': timestamp_to_datetime(os.stat(path).st_mtime)}])

    def test_list_folder_content(self):
        path = tempfile.mkdtemp(dir=self.path)
        _, filepath = tempfile.mkstemp(dir=path)
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.data, [{'type': 'file', 'name': os.path.basename(filepath), 'size': os.stat(filepath).st_size, 'modified': timestamp_to_datetime(os.stat(filepath).st_mtime)}])

    def test_illegal_path(self):
        path = os.path.join(self.path, '..')
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_existing_path(self):
        path = os.path.join(self.path, 'does/not/exist')
        res = self.client.get(self.url, {'type': 'access', 'path': path})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_to_dip_not_responsible(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        ip = InformationPackage.objects.create(object_path=dstdir, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_file(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        ip = InformationPackage.objects.create(object_path=dstdir, responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_file_overwrite(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo.txt'

        open(os.path.join(dstdir, dst), 'a').close()

        ip = InformationPackage.objects.create(object_path=dstdir, responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst)))

    def test_add_to_dip_file_to_dir(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        _, src = tempfile.mkstemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = os.path.basename(tempfile.mkdtemp(dir=dstdir))

        ip = InformationPackage.objects.create(object_path=dstdir, responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isfile(os.path.join(dstdir, dst, os.path.basename(src))))

    def test_add_to_dip_dir_to_dir(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        src = tempfile.mkdtemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = 'foo'

        ip = InformationPackage.objects.create(object_path=dstdir, responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isdir(os.path.join(dstdir, dst)))

    def test_add_to_dip_dir_to_dir_overwrite(self):
        self.url = self.url + 'add-to-dip/'

        srcdir = tempfile.mkdtemp(dir=self.path)
        src = tempfile.mkdtemp(dir=srcdir)

        dstdir = tempfile.mkdtemp(dir=self.path)
        dst = os.path.basename(tempfile.mkdtemp(dir=dstdir))

        ip = InformationPackage.objects.create(object_path=dstdir, responsible=self.user, package_type=InformationPackage.DIP)

        res = self.client.post(self.url, {'type': 'access', 'src': src, 'dst': dst, 'dip': str(ip.pk)})

        self.assertTrue(os.path.isdir(os.path.join(dstdir, dst)))


class InformationPackageViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse('informationpackage-list')

    def test_empty(self):
        res = self.client.get(self.url)
        self.assertEqual(res.data, [])

    def test_aic_view_type_aic_no_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)

        res = self.client.get(self.url, data={'view_type': 'aic'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_one_in_workarea(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)

        Path.objects.create(entity='access_workarea', value='access')
        Workarea.objects.create(user=self.user, ip=aip2, type=Workarea.ACCESS, read_only=False)

        res = self.client.get(self.url, data={'view_type': 'aic'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_aic_view_type_aic_multiple_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic'})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)

    def test_aic_view_type_aic_multiple_aips_same_state_empty_filter(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': ''})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)

        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip2.pk))

    def test_aic_view_type_aic_multiple_aips_filter_responsible(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(responsible=self.user, generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'responsible': self.user.username})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))

        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_aic_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_aic_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(state='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_no_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)

        res = self.client.get(self.url, data={'view_type': 'ip'})
        self.assertEqual(len(res.data), 0)

    def test_ip_view_type_aic_multiple_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=0, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, state='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip3.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, state='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_multiple_aips_different_states_first_ip_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_all_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, state='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, state='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 0)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'bar'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_multiple_aips_different_labels_all_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, label='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, label='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic1.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip11.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip11.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search_and_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, label='foo', state='first', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, label='bar', state='second', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'bar', 'state': 'second'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_aic_view_type_aic_aips_different_labels_same_aic_global_search(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(label='first', package_type=InformationPackage.AIP, aic=aic, generation=0)
        aip2 = InformationPackage.objects.create(label='second', package_type=InformationPackage.AIP, aic=aic, generation=1)

        res = self.client.get(self.url, {'view_type': 'aic', 'search': 'first'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_aic_view_type_dip(self):
        dip = InformationPackage.objects.create(package_type=InformationPackage.DIP, generation=0)

        res = self.client.get(self.url, {'view_type': 'aic'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(dip.pk))

    def test_ip_view_type_dip(self):
        dip = InformationPackage.objects.create(package_type=InformationPackage.DIP)

        res = self.client.get(self.url, {'view_type': 'ip'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(dip.pk))

    @mock.patch('ip.views.shutil.rmtree')
    @mock.patch('ip.views.os.remove')
    def test_delete_ip_without_permission(self, mock_os, mock_shutil):
        ip = InformationPackage.objects.create(object_path='foo')
        url = reverse('informationpackage-detail', args=(str(ip.pk),))
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        mock_shutil.assert_not_called()
        mock_os.assert_not_called()

    @mock.patch('ip.views.shutil.rmtree')
    @mock.patch('ip.views.os.remove')
    def test_delete_ip_with_permission(self, mock_os, mock_shutil):
        ip = InformationPackage.objects.create(object_path='foo', responsible=self.user)
        url = reverse('informationpackage-detail', args=(str(ip.pk),))
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        mock_shutil.assert_called_once_with(ip.object_path)
        mock_os.assert_not_called()

    @mock.patch('ip.views.shutil.rmtree')
    @mock.patch('ip.views.os.remove')
    def test_delete_archived_ip(self, mock_os, mock_shutil):
        ip = InformationPackage.objects.create(object_path='foo', responsible=self.user, archived=True)
        url = reverse('informationpackage-detail', args=(str(ip.pk),))
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_shutil.assert_not_called()
        mock_os.assert_not_called()

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_no_label(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_prepare.assert_not_called()

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_no_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url, {'label': 'foo'})

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value=None, orders=[])

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'
        res = self.client.post(self.url, {'label': 'foo', 'object_identifier_value': 'bar'})

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value='bar', orders=[])

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_existing_object_identifier_value(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        InformationPackage.objects.create(object_identifier_value='bar')
        res = self.client.post(self.url, {'label': 'foo', 'object_identifier_value': 'bar'})

        mock_prepare.assert_not_called()

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_orders(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        orders = [str(Order.objects.create(responsible=self.user).pk)]
        res = self.client.post(self.url, {'label': 'foo', 'orders': orders}, format='json')

        mock_prepare.assert_called_once_with(label='foo', object_identifier_value=None, orders=orders)

    @mock.patch('workflow.tasks.PrepareDIP.run', side_effect=lambda *args, **kwargs: None)
    def test_prepare_dip_with_non_existing_order(self, mock_prepare):
        self.url = self.url + 'prepare-dip/'

        orders = [str(Order.objects.create(responsible=self.user).pk), str(uuid.uuid4())]
        res = self.client.post(self.url, {'label': 'foo', 'orders': orders}, format='json')

        mock_prepare.assert_not_called()

    @mock.patch('workflow.tasks.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_preserve_aip(self, mock_step):
        self.ip = InformationPackage.objects.create(package_type=InformationPackage.AIP)
        self.url = reverse('informationpackage-detail', args=(self.ip.pk,))
        self.url = self.url + 'preserve/'

        self.client.post(self.url)
        mock_step.assert_called_once()

        self.assertTrue(ProcessStep.objects.filter(information_package=self.ip).exists())

    @mock.patch('workflow.tasks.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_preserve_dip(self, mock_step):
        cache = Path.objects.create(entity='cache', value='cache')
        ingest = Path.objects.create(entity='ingest', value='ingest')
        policy = ArchivePolicy.objects.create(cache_storage=cache, ingest_path=ingest)

        self.ip = InformationPackage.objects.create(package_type=InformationPackage.DIP)
        self.url = reverse('informationpackage-detail', args=(self.ip.pk,))
        self.url = self.url + 'preserve/'

        self.client.post(self.url, {'policy': str(policy.pk)})
        mock_step.assert_called_once()

        self.assertTrue(ProcessStep.objects.filter(information_package=self.ip).exists())


class InformationPackageViewSetFilesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin", password='admin')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.datadir = tempfile.mkdtemp()

        self.ip = InformationPackage.objects.create(object_path=self.datadir, package_type=InformationPackage.DIP)
        self.url = reverse('informationpackage-detail', args=(str(self.ip.pk),))
        self.url = self.url + 'files/'

    def tearDown(self):
        try:
            shutil.rmtree(self.datadir)
        except:
            pass

    def test_delete_file(self):
        _, path = tempfile.mkstemp(dir=self.datadir)
        res = self.client.delete(self.url, {'path': path})

        self.assertFalse(os.path.exists(path))

    def test_delete_folder(self):
        path = tempfile.mkdtemp(dir=self.datadir)
        res = self.client.delete(self.url, {'path': path})

        self.assertFalse(os.path.exists(path))

    def test_delete_no_path(self):
        res = self.client.delete(self.url)
        res.status = status.HTTP_400_BAD_REQUEST

    @mock.patch('ESSArch_Core.ip.models.InformationPackage.files', return_value=HttpResponse())
    def test_list_file(self, mock_files):
        _, path = tempfile.mkstemp(dir=self.datadir)
        self.client.get(self.url)

        mock_files.assert_called_once_with('')

    @mock.patch('ESSArch_Core.ip.models.InformationPackage.files', return_value=HttpResponse())
    def test_list_folder(self, mock_files):
        path = tempfile.mkdtemp(dir=self.datadir)
        self.client.get(self.url)

        mock_files.assert_called_once_with('')

    @mock.patch('ESSArch_Core.ip.models.InformationPackage.files', return_value=HttpResponse())
    def test_list_folder_content(self, mock_files):
        path = tempfile.mkdtemp(dir=self.datadir)
        _, filepath = tempfile.mkstemp(dir=path)
        self.client.get(self.url, {'path': path})

        mock_files.assert_called_once_with(path)

    def test_create_folder(self):
        path = 'foo'
        res = self.client.post(self.url, {'path': path, 'type': 'dir'})

        self.assertTrue(os.path.isdir(os.path.join(self.ip.object_path, path)))

    def test_create_file(self):
        path = 'foo.txt'
        res = self.client.post(self.url, {'path': path, 'type': 'file'})

        self.assertTrue(os.path.isfile(os.path.join(self.ip.object_path, path)))

class InformationPackageReceptionViewSetTestCase(TestCase):
    def setUp(self):
        self.cache = Path.objects.create(entity='cache', value='cache')
        self.ingest = Path.objects.create(entity='ingest', value='ingest')

        self.user = User.objects.create(username="admin", password='admin')
        self.policy = ArchivePolicy.objects.create(cache_storage=self.cache, ingest_path=self.ingest)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.url = reverse('ip-reception-list')

        self.datadir = tempfile.mkdtemp()
        Path.objects.create(entity='reception', value=self.datadir)

        self.sa = SubmissionAgreement.objects.create()
        aip_profile = Profile.objects.create(profile_type='aip')
        ProfileSA.objects.create(submission_agreement=self.sa, profile=aip_profile)

        self.tar_filepath = os.path.join(self.datadir, '1.tar')
        self.xml_filepath = os.path.join(self.datadir, '1.xml')

        open(self.tar_filepath, 'a').close()
        with open(self.xml_filepath, 'w') as xml:
            xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
            <root OBJID="1" LABEL="my label">
                <metsHdr/>
                <file><FLocat href="file:///1.tar"/></file>
            </root>
            ''')

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive(self, mock_receive, mock_find_dest):
        data = {'archive_policy': str(self.policy.pk), 'submission_agreement': self.sa.pk}
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        mock_receive.assert_called_once()

    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_existing(self, mock_receive):
        data = {'archive_policy': str(self.policy.pk), 'submission_agreement': self.sa.pk}
        InformationPackage.objects.create(object_identifier_value='1')
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        mock_receive.assert_not_called()

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_no_sa(self, mock_receive, mock_find_dest):
        data = {'archive_policy': str(self.policy.pk)}
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_non_existing_sa_in_xml(self, mock_receive, mock_find_dest):
        with open(self.xml_filepath, 'w') as xml:
            xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
            <root OBJID="1" LABEL="my label">
                <metsHdr>
                    <altRecordID TYPE="SUBMISSIONAGREEMENT">%s</altRecordID>
                </metsHdr>
                <file><FLocat href="file:///1.tar"/></file>
            </root>
            ''' % str(uuid.uuid4()))

        data = {'archive_policy': str(self.policy.pk)}

        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_sa_in_xml_and_no_provided(self, mock_receive, mock_find_dest):
        with open(self.xml_filepath, 'w') as xml:
            xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
            <root OBJID="1" LABEL="my label">
                <metsHdr>
                    <altRecordID TYPE="SUBMISSIONAGREEMENT">%s</altRecordID>
                </metsHdr>
                <file><FLocat href="file:///1.tar"/></file>
            </root>
            ''' % str(self.sa.pk))

        data = {'archive_policy': str(self.policy.pk)}
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_sa_in_xml_and_provided_match(self, mock_receive, mock_find_dest):
        with open(self.xml_filepath, 'w') as xml:
            xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
            <root OBJID="1" LABEL="my label">
                <metsHdr>
                    <altRecordID TYPE="SUBMISSIONAGREEMENT">%s</altRecordID>
                </metsHdr>
                <file><FLocat href="file:///1.tar"/></file>
            </root>
            ''' % str(self.sa.pk))

        data = {'archive_policy': str(self.policy.pk), 'submission_agreement': self.sa.pk}
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_sa_in_xml_and_provided_not_match(self, mock_receive, mock_find_dest):
        new_sa = SubmissionAgreement.objects.create()

        with open(self.xml_filepath, 'w') as xml:
            xml.write('''<?xml version="1.0" encoding="UTF-8" ?>
            <root OBJID="1" LABEL="my label">
                <metsHdr>
                    <altRecordID TYPE="SUBMISSIONAGREEMENT">%s</altRecordID>
                </metsHdr>
                <file><FLocat href="file:///1.tar"/></file>
            </root>
            ''' % str(new_sa.pk))

        data = {'archive_policy': str(self.policy.pk), 'submission_agreement': self.sa.pk}
        res = self.client.post(self.url + '1/receive/', data=data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_invalid_validator(self, mock_receive, mock_find_dest):
        data = {'archive_policy': str(self.policy.pk), 'validators': {'validate_invalid': True}, 'submission_agreement': self.sa.pk}
        res = self.client.post(self.url + '1/receive/', data=data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(ProcessStep.objects.filter(name='Validate').exists())
        mock_receive.assert_called_once()

    @mock.patch('ip.views.find_destination', return_value=('foo', 'bar'))
    @mock.patch('ip.views.ProcessStep.run', side_effect=lambda *args, **kwargs: None)
    def test_receive_validator(self, mock_receive, mock_find_dest):
        data = {'archive_policy': str(self.policy.pk), 'validators': {'validate_xml_file': True}, 'submission_agreement': self.sa.pk}
        res = self.client.post(self.url + '1/receive/', data=data)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(ProcessStep.objects.filter(name='Validate').exists())
        self.assertTrue(ProcessTask.objects.filter(name='workflow.tasks.ValidateXMLFile').exists())
        mock_receive.assert_called_once()


class OrderViewSetTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_empty(self):
        url = reverse('order-list')
        res = self.client.get(url)

        self.assertEqual(res.data, [])

    def test_list_only_owned(self):
        other_user = User.objects.create(username="user")
        order = Order.objects.create(responsible=self.user)
        other_order = Order.objects.create(responsible=other_user)

        url = reverse('order-list')
        res = self.client.get(url)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(order.pk))

    def test_list_all_if_superuser(self):
        other_user = User.objects.create(username="user")
        order = Order.objects.create(responsible=self.user)
        other_order = Order.objects.create(responsible=other_user)

        self.user.is_superuser = True
        self.user.save()

        url = reverse('order-list')
        res = self.client.get(url)

        self.assertEqual(len(res.data), 2)

    def test_detail_owned(self):
        order = Order.objects.create(responsible=self.user)

        url = reverse('order-detail', args=[order.pk])
        res = self.client.get(url)

        self.assertEqual(res.data['id'], str(order.pk))

    def test_detail_non_existing(self):
        url = reverse('order-detail', args=[uuid.uuid4()])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_deny_detail_other(self):
        other_user = User.objects.create(username="user")
        order = Order.objects.create(responsible=other_user)

        url = reverse('order-detail', args=[order.pk])
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_other_super_user(self):
        other_user = User.objects.create(username="user")
        order = Order.objects.create(responsible=other_user)

        self.user.is_superuser = True
        self.user.save()

        url = reverse('order-detail', args=[order.pk])
        res = self.client.get(url)

        self.assertEqual(res.data['id'], str(order.pk))

    def test_create_without_ip(self):
        url = reverse('order-list')
        res = self.client.post(url, {'label': 'foo'})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['label'], 'foo')
        self.assertTrue(Order.objects.filter(label='foo', responsible=self.user).exists())

    def test_create_with_dip(self):
        url = reverse('order-list')
        ip = InformationPackage.objects.create(package_type=InformationPackage.DIP)
        ip_url = reverse('informationpackage-detail', args=[ip.pk])
        res = self.client.post(url, {'label': 'foo', 'information_packages': [ip_url]})

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.first().information_packages.first(), ip)

    def test_create_with_ip_other_than_dip(self):
        url = reverse('order-list')
        ip = InformationPackage.objects.create(package_type=InformationPackage.SIP)
        ip_url = reverse('informationpackage-detail', args=[ip.pk])
        res = self.client.post(url, {'label': 'foo', 'information_packages': [ip_url]})

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
