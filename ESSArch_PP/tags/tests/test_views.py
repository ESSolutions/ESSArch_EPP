from unittest import mock

from countries_plus.models import Country
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from languages_plus.models import Language
from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.agents.models import (
    Agent,
    AgentTagLink,
    AgentTagLinkRelationType,
    AgentType,
    MainAgentType,
    RefCode,
)
from ESSArch_Core.auth.models import GroupType, Group
from ESSArch_Core.tags.models import (
    Tag,
    TagVersion,
    TagVersionType,
)

User = get_user_model()


class AgentArchiveRelationTests(TestCase):
    fixtures = ['countries_data', 'languages_data']

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(username='user')
        self.member = self.user.essauth_member

        self.client.force_authenticate(user=self.user)

        self.archive_type = TagVersionType.objects.create(name='archive', archive_type=True)

        self.main_agent_type = MainAgentType.objects.create()
        self.agent_type = AgentType.objects.create(main_type=self.main_agent_type)

        self.relation_type = AgentTagLinkRelationType.objects.create(name='test')

        self.ref_code = RefCode.objects.create(
            country=Country.objects.get(iso='SE'),
            repository_code='repo',
        )

    def create_agent(self):
        return Agent.objects.create(
            level_of_detail=Agent.MINIMAL,
            script=Agent.LATIN,
            language=Language.objects.get(iso_639_1='sv'),
            record_status=Agent.DRAFT,
            type=self.agent_type,
            ref_code=self.ref_code,
            create_date=timezone.now(),
        )

    def create_archive(self):
        tag = Tag.objects.create()
        tag_version = TagVersion.objects.create(
            tag=tag,
            elastic_index='archive',
            type=self.archive_type,
        )
        return tag_version

    def test_add_relation(self):
        agent = self.create_agent()
        archive = self.create_archive()

        url = reverse('agent-archives-list', args=[agent.pk])

        response = self.client.post(
            url,
            data={
                'archive': archive.pk,
                'type': self.relation_type.pk,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AgentTagLink.objects.count(), 1)
        self.assertTrue(AgentTagLink.objects.filter(agent=agent, tag=archive, type=self.relation_type).exists())

    def test_add_same_relation_twice(self):
        agent = self.create_agent()
        archive = self.create_archive()

        url = reverse('agent-archives-list', args=[agent.pk])

        response = self.client.post(
            url,
            data={
                'archive': archive.pk,
                'type': self.relation_type.pk,
            }
        )

        response = self.client.post(
            url,
            data={
                'archive': archive.pk,
                'type': self.relation_type.pk,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AgentTagLink.objects.count(), 1)

    def test_update_relation(self):
        agent = self.create_agent()
        archive = self.create_archive()
        relation = AgentTagLink.objects.create(
            agent=agent,
            tag=archive,
            type=self.relation_type,
            description='foo',
        )

        url = reverse('agent-archives-detail', args=[agent.pk, relation.pk])
        response = self.client.patch(
            url,
            data={
                'description': 'bar',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AgentTagLink.objects.count(), 1)
        self.assertTrue(
            AgentTagLink.objects.filter(
                agent=agent,
                tag=archive,
                type=self.relation_type,
                description='bar',
            ).exists()
        )

    def test_delete_relation(self):
        agent = self.create_agent()
        archive = self.create_archive()
        relation = AgentTagLink.objects.create(
            agent=agent,
            tag=archive,
            type=self.relation_type,
        )

        url = reverse('agent-archives-detail', args=[agent.pk, relation.pk])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AgentTagLink.objects.count(), 0)


class CreateArchiveTests(TestCase):
    fixtures = ['countries_data', 'languages_data']

    @classmethod
    def setUpTestData(cls):
        cls.org_group_type = GroupType.objects.create(codename='organization')
        cls.archive_type = TagVersionType.objects.create(name='archive', archive_type=True)
        cls.url = reverse('search-list')

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(username='user')
        self.member = self.user.essauth_member

        group = Group.objects.create(name='organization', group_type=self.org_group_type)
        group.add_member(self.member)

        self.client.force_authenticate(user=self.user)

    def test_without_permission(self):
        response = self.client.post(
            self.url,
            data={
                'index': 'archive',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('tags.search.TagVersionNestedSerializer')
    @mock.patch('tags.search.ArchiveWriteSerializer')
    def test_with_permission(self, mock_write_serializer, mock_tag_serializer):
        self.user.user_permissions.add(Permission.objects.get(codename="create_archive"))
        self.user = User.objects.get(username="user")
        self.client.force_authenticate(user=self.user)

        mock_tag_serializer().data = {}

        response = self.client.post(
            self.url,
            data={
                'index': 'archive',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_write_serializer.assert_called_once()


class CreateComponentTests(TestCase):
    fixtures = ['countries_data', 'languages_data']

    @classmethod
    def setUpTestData(cls):
        cls.org_group_type = GroupType.objects.create(codename='organization')
        cls.tag_type = TagVersionType.objects.create(name='volume', archive_type=False)
        cls.url = reverse('search-list')

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(username='user')
        self.member = self.user.essauth_member

        group = Group.objects.create(name='organization', group_type=self.org_group_type)
        group.add_member(self.member)

        self.client.force_authenticate(user=self.user)

    def test_without_permission(self):
        response = self.client.post(
            self.url,
            data={
                'index': 'component',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('tags.search.TagVersionNestedSerializer')
    @mock.patch('tags.search.ComponentWriteSerializer')
    def test_with_permission(self, mock_write_serializer, mock_tag_serializer):
        self.user.user_permissions.add(Permission.objects.get(codename="add_tag"))
        self.user = User.objects.get(username="user")
        self.client.force_authenticate(user=self.user)

        mock_tag_serializer().data = {}

        response = self.client.post(
            self.url,
            data={
                'index': 'component',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_write_serializer.assert_called_once()


class DeleteTagTests(TestCase):
    fixtures = ['countries_data', 'languages_data']

    @classmethod
    def setUpTestData(cls):
        cls.org_group_type = GroupType.objects.create(codename='organization')

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create(username='user')
        self.member = self.user.essauth_member

        group = Group.objects.create(name='organization', group_type=self.org_group_type)
        group.add_member(self.member)

        self.client.force_authenticate(user=self.user)

    def test_delete_archive_without_permission(self):
        archive_tag = Tag.objects.create()
        archive_type = TagVersionType.objects.create(name='archive', archive_type=True)
        archive_tag_version = TagVersion.objects.create(tag=archive_tag, type=archive_type, elastic_index='archive')

        url = reverse('search-detail', args=(archive_tag_version.pk,))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_archive_with_permission(self):
        self.user.user_permissions.add(Permission.objects.get(codename="delete_archive"))
        self.user = User.objects.get(username="user")
        self.client.force_authenticate(user=self.user)

        archive_tag = Tag.objects.create()
        archive_type = TagVersionType.objects.create(name='archive', archive_type=True)
        archive_tag_version = TagVersion.objects.create(tag=archive_tag, type=archive_type, elastic_index='archive')

        url = reverse('search-detail', args=(archive_tag_version.pk,))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_component_without_permission(self):
        tag = Tag.objects.create()
        tag_type = TagVersionType.objects.create(name='volume', archive_type=False)
        tag_version = TagVersion.objects.create(tag=tag, type=tag_type, elastic_index='component')

        url = reverse('search-detail', args=(tag_version.pk,))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_component_with_permission(self):
        self.user.user_permissions.add(Permission.objects.get(codename="delete_tag"))
        self.user = User.objects.get(username="user")
        self.client.force_authenticate(user=self.user)

        tag = Tag.objects.create()
        tag_type = TagVersionType.objects.create(name='volume', archive_type=False)
        tag_version = TagVersion.objects.create(tag=tag, type=tag_type, elastic_index='component')

        url = reverse('search-detail', args=(tag_version.pk,))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
