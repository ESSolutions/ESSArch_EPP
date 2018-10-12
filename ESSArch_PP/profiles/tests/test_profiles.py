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

from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.ip.models import ArchivistOrganization, InformationPackage

from ESSArch_Core.profiles.models import Profile, SubmissionAgreement


class LockSubmissionAgreement(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.sa = SubmissionAgreement.objects.create()

    def test_lock_to_ip_without_permission(self):
        ip = InformationPackage.objects.create(submission_agreement=self.sa)

        res = self.client.post('/api/submission-agreements/%s/lock/' % str(self.sa.pk), {'ip': str(ip.pk)})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_lock_to_ip_with_permission(self):
        ip = InformationPackage.objects.create(responsible=self.user, submission_agreement=self.sa)

        res = self.client.post('/api/submission-agreements/%s/lock/' % str(self.sa.pk), {'ip': str(ip.pk)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(ArchivistOrganization.objects.exists())

    def test_new_archivist_organization(self):
        ip = InformationPackage.objects.create(responsible=self.user, submission_agreement=self.sa)
        self.sa.archivist_organization = 'ao'
        self.sa.save()

        self.client.post('/api/submission-agreements/%s/lock/' % str(self.sa.pk), {'ip': str(ip.pk)})

        ip.refresh_from_db()
        self.assertEqual(ip.archivist_organization.name, 'ao')

    def test_existing_archivist_organization(self):
        ip = InformationPackage.objects.create(responsible=self.user, submission_agreement=self.sa)
        ArchivistOrganization.objects.create(name='ao')

        self.sa.archivist_organization = 'ao'
        self.sa.save()

        self.client.post('/api/submission-agreements/%s/lock/' % str(self.sa.pk), {'ip': str(ip.pk)})

        ip.refresh_from_db()
        self.assertEqual(ip.archivist_organization.name, 'ao')
        self.assertEqual(ArchivistOrganization.objects.count(), 1)


class SaveSubmissionAgreement(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        content_type = ContentType.objects.get_for_model(SubmissionAgreement)
        perm = Permission.objects.get(
            codename='create_new_sa_generation',
            content_type=content_type,
        )
        self.user.user_permissions.add(perm)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.sa = SubmissionAgreement.objects.create()
        self.ip = InformationPackage.objects.create()

    def test_save_no_name(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)

        data = {
            'data': {'archivist_organization': 'new ao'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubmissionAgreement.objects.count(), 1)

    def test_save_empty_name(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)

        data = {
            'new_name': '',
            'data': {'archivist_organization': 'new ao'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubmissionAgreement.objects.count(), 1)

    def test_save_no_changes(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)
        self.sa.archivist_organization = 'initial'
        self.sa.save()

        data = {
            'new_name': 'new',
            'data': {'archivist_organization': 'initial'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubmissionAgreement.objects.count(), 1)

    def test_save_empty_required_value(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)
        self.sa.archivist_organization = ''
        self.sa.template = [
            {
                "key": "archivist_organization",
                "templateOptions": {
                    "required": True,
                },
            }
        ]
        self.sa.save()

        data = {
            'new_name': 'new',
            'data': {'archivist_organization': '', 'label': 'new_data'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubmissionAgreement.objects.count(), 1)

    def test_save_missing_required_value(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)
        self.sa.archivist_organization = ''
        self.sa.template = [
            {
                "key": "archivist_organization",
                "templateOptions": {
                    "required": True,
                },
            }
        ]
        self.sa.save()

        data = {
            'new_name': 'new',
            'data': {'label': 'new_data'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubmissionAgreement.objects.count(), 1)

    def test_save_changes(self):
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)
        self.sa.archivist_organization = 'initial'
        self.sa.save()

        data = {
            'new_name': 'new',
            'data': {'archivist_organization': 'new ao'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(SubmissionAgreement.objects.filter(name='', archivist_organization='initial').exists())
        self.assertTrue(SubmissionAgreement.objects.filter(name='new', archivist_organization='new ao').exists())

    def test_save_changes_without_permission(self):
        self.user.user_permissions.all().delete()
        url = '/api/submission-agreements/%s/save/' % str(self.sa.pk)
        self.sa.archivist_organization = 'initial'
        self.sa.save()

        data = {
            'new_name': 'new',
            'data': {'archivist_organization': 'new ao'},
            'information_package': str(self.ip.pk),
        }

        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class SaveProfile(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_save_no_changes(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'initial'},
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': profile.specification_data,
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_profile(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'initial'},
            template=[
                {
                    "key": "email",
                    "templateOptions": {
                        "type": "email"
                    },
                },
                {
                    "key": "url",
                    "templateOptions": {
                        "type": "url"
                    },
                },
                {
                    "key": "remote",
                    "templateOptions": {
                        "type": "url",
                        "remote": ""
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {
                'foo': 'updated', 'email': 'foo@example.com', 'url': 'http://example.com',
                'remote': 'http://example.com,admin,admin',
            },
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_save_empty_required_value(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'initial'},
            template=[
                {
                    "key": "foo",
                    "templateOptions": {
                        "required": True,
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {'foo': ''},
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_missing_required_value(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'initial'},
            template=[
                {
                    "key": "foo",
                    "templateOptions": {
                        "required": True,
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {},
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_invalid_email(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'initial@example.com'},
            template=[
                {
                    "key": "foo",
                    "templateOptions": {
                        "type": "email"
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {'foo': 'invalid'},
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_invalid_url(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'http://example.com'},
            template=[
                {
                    "key": "foo",
                    "templateOptions": {
                        "type": "url"
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {'foo': 'invalid'},
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_save_invalid_remote_url(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='sip',
            specification_data={'foo': 'http://example.com,admin,admin'},
            template=[
                {
                    "key": "foo",
                    "templateOptions": {
                        "type": "url",
                        "remote": ""
                    },
                }
            ]
        )

        profile_url = reverse('profile-detail', args=(profile.pk,))
        save_url = '%ssave/' % profile_url

        data = {
            'new_name': 'second',
            'specification_data': {'foo': 'invalid'},
            'structure': {},
        }

        res = self.client.post(save_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class LockProfile(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.sa = SubmissionAgreement.objects.create()
        self.ip = InformationPackage.objects.create(
            submission_agreement=self.sa,
            submission_agreement_locked=True,
        )

    def test_lock_profile(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='test',
            specification_data={
                'first': 'initial'
            },
            template=[
                {
                    "templateOptions": {
                        "type": "text",
                    },
                    "defaultValue": "foo",
                    "type": "input",
                    "key": "first"
                },
                {
                    "templateOptions": {
                        "type": "text",
                    },
                    "defaultValue": "bar",
                    "type": "input",
                    "key": "second"
                },
                {
                    "templateOptions": {
                        "type": "text",
                    },
                    "type": "input",
                    "key": "third"
                },
            ]
        )

        url = reverse('profile-detail', args=(profile.pk,))
        url = url + 'lock/'

        res = self.client.post(url, {'information_package': self.ip.pk})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.specification_data['first'], 'initial')
        self.assertEqual(profile.specification_data['second'], 'bar')

    def test_lock_profile_without_ip(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='test',
            specification_data={},
            template=[]
        )

        url = reverse('profile-detail', args=(profile.pk,))
        url = url + 'lock/'

        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lock_profile_twice(self):
        profile = Profile.objects.create(
            name='first',
            profile_type='test',
            specification_data={},
            template=[]
        )

        url = reverse('profile-detail', args=(profile.pk,))
        url = url + 'lock/'

        res = self.client.post(url, {'information_package': self.ip.pk})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        res = self.client.post(url, {'information_package': self.ip.pk})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
