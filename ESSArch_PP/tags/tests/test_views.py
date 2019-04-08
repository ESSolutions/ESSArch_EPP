from countries_plus.models import Country
from django.contrib.auth import get_user_model
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

    def test_add_agent_end_date_before_archive_start_date(self):
        agent = self.create_agent()
        agent.end_date = "2019-01-01"
        agent.save()

        archive = self.create_archive()
        archive.start_date = "2020-01-01"
        archive.save()

        url = reverse('agent-archives-list', args=[agent.pk])

        response = self.client.post(
            url,
            data={
                'archive': archive.pk,
                'type': self.relation_type.pk,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AgentTagLink.objects.count(), 0)

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
