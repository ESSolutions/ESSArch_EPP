from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from ESSArch_Core.WorkflowEngine.models import (
    ProcessStep, ProcessTask,
)


class UndoTaskTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.task = ProcessTask.objects.create(name='ESSArch_Core.WorkflowEngine.tests.tasks.First')
        self.url = reverse('processtask-detail', args=(str(self.task.pk),)) + 'undo/'

    def test_undo_without_permissions(self):
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ProcessTask.objects.filter(pk=self.task.pk, undone__isnull=False).exists())

    def test_undo_with_permissions(self):
        self.user.user_permissions.add(Permission.objects.get(codename='can_undo'))

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(ProcessTask.objects.filter(pk=self.task.pk, undone__isnull=False).exists())
        self.assertTrue(ProcessTask.objects.filter(undone_task=self.task, undo_type=True).exists())


class RetryTaskTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.task = ProcessTask.objects.create(name='ESSArch_Core.WorkflowEngine.tests.tasks.First')
        self.url = reverse('processtask-detail', args=(str(self.task.pk),)) + 'retry/'

    def test_retry_without_permissions(self):
        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ProcessTask.objects.filter(pk=self.task.pk, retried__isnull=False).exists())

    def test_retry_with_permissions(self):
        self.user.user_permissions.add(Permission.objects.get(codename='can_retry'))

        res = self.client.post(self.url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(ProcessTask.objects.filter(pk=self.task.pk, retried__isnull=False).exists())
        self.assertTrue(ProcessTask.objects.filter(retried_task=self.task).exists())


class UndoStepTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.step = ProcessStep.objects.create()
        task = ProcessTask.objects.create(
            name='ESSArch_Core.WorkflowEngine.tests.tasks.First',
            processstep=self.step,
        )
        self.url = reverse('processstep-detail', args=(str(self.step.pk),)) + 'undo/'

    def test_undo_without_permissions(self):
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_undo_with_permissions(self):
        self.user.user_permissions.add(Permission.objects.get(codename='can_undo'))

        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class RetryStepTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="admin")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.step = ProcessStep.objects.create()
        task = ProcessTask.objects.create(
            name='ESSArch_Core.WorkflowEngine.tests.tasks.First',
            processstep=self.step,
        )
        undo_task = ProcessTask.objects.create(
            name='ESSArch_Core.WorkflowEngine.tests.tasks.First',
            processstep=self.step, undone_task=task, undo_type=True,
        )
        task.save()
        self.url = reverse('processstep-detail', args=(str(self.step.pk),)) + 'retry/'

    def test_retry_without_permissions(self):
        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_retry_with_permissions(self):
        self.user.user_permissions.add(Permission.objects.get(codename='can_retry'))

        res = self.client.post(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
