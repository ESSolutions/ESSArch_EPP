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

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

import mock

from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.ip.models import InformationPackage, Workarea


class AccessTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.root = os.path.dirname(os.path.realpath(__file__))
        self.datadir = os.path.join(self.root, 'datadir')

        self.ip = InformationPackage.objects.create(ObjectPath=self.datadir)
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

        self.ip = InformationPackage.objects.create()
        self.url = reverse('workarea-list')

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

    def test_ip_in_workarea_by_current_user(self):
        Workarea.objects.create(user=self.user, ip=self.ip, type=Workarea.ACCESS)

        res = self.client.get(self.url, {'type': 'access'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]['id'], str(self.ip.pk))

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
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(res.data[0]['information_packages'], [])

    def test_aic_view_type_aic_multiple_aips(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)

    def test_aic_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))

    def test_aic_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(State='bar', aic=aic, package_type=InformationPackage.AIP)

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

        res = self.client.get(self.url, data={'view_type': 'ip'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_same_state_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip3.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)
        aip3 = InformationPackage.objects.create(generation=2, State='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)

    def test_ip_view_type_aic_multiple_aips_different_states_first_ip_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='foo', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_different_states_all_filter_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, State='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, State='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'state': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_all_filter_label(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='bar', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='baz', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'label': 'foo'})
        self.assertEqual(len(res.data), 0)

    def test_aic_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, Label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, Label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, Label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, Label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'aic', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aic1.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 2)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip11.pk))
        self.assertEqual(res.data[0]['information_packages'][1]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search(self):
        aic1 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip11 = InformationPackage.objects.create(generation=0, Label='first1', aic=aic1, package_type=InformationPackage.AIP)
        aip12 = InformationPackage.objects.create(generation=1, Label='first2', aic=aic1, package_type=InformationPackage.AIP)

        aic2 = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip21 = InformationPackage.objects.create(generation=0, Label='second1', aic=aic2, package_type=InformationPackage.AIP)
        aip22 = InformationPackage.objects.create(generation=1, Label='second2', aic=aic2, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip11.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip12.pk))

    def test_ip_view_type_aic_multiple_aips_different_labels_global_search_and_state(self):
        aic = InformationPackage.objects.create(package_type=InformationPackage.AIC)
        aip = InformationPackage.objects.create(generation=0, Label='foo', State='first', aic=aic, package_type=InformationPackage.AIP)
        aip2 = InformationPackage.objects.create(generation=1, Label='bar', State='second', aic=aic, package_type=InformationPackage.AIP)

        res = self.client.get(self.url, data={'view_type': 'ip', 'search': 'foo', 'state': 'first'})
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(aip.pk))
        self.assertEqual(len(res.data[0]['information_packages']), 1)
        self.assertEqual(res.data[0]['information_packages'][0]['id'], str(aip2.pk))
