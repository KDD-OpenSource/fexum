from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN, HTTP_204_NO_CONTENT
from users.tests.factories import UserFactory
from tasks.tests.factories import task_factory
from django.conf import settings
from unittest.mock import patch


class TestTaskListView(APITestCase):
    def setUp(self):
        # run celery task synchronous
        settings.CELERY_ALWAYS_EAGER = True

    def test_retrieve_task_list(self):
        url = reverse('task-list')
        task_factory.apply_async(countdown=60)

        self.client.force_login(user=UserFactory())
        response = self.client.get(url)
        response_data = response.json()

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response_data.pop('reserved'), {})
        self.assertEqual(response_data.pop('active'), {})
        self.assertNotEqual(response_data.pop('scheduled'), {})
        self.assertEqual(len(response_data), 0)

    def test_retrieve_task_list_unauthenticated(self):
        url = reverse('task-list')

        response = self.client.get(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})


class TestTaskTerminateView(APITestCase):
    def test_terminate_task(self):
        task_id = '9cd8eaca-6d2a-4567-961b-b15c2290fb56'
        url = reverse('task-terminate', args=[task_id])
        self.client.force_login(user=UserFactory())

        with patch('tasks.views.revoke') as revoke_task:
            response = self.client.delete(url)
            revoke_task.assert_called_once_with(task_id, terminate=True)

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')

    def test_terminate_task_unauthenticated(self):
        task_id = '9cd8eaca-6d2a-4567-961b-b15c2290fb56'
        url = reverse('task-terminate', args=[task_id])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(response.json(),
                         {'detail': 'Authentication credentials were not provided.'})