from django.urls import reverse
from django.test import TestCase


class TestTaskListUrl(TestCase):
    def test_task_list_url(self):
        url = reverse('task-list')
        self.assertEqual(url, '/api/tasks')


class TestTaskTerminateUrl(TestCase):
    def test_task_terminate_url(self):
        task_id = '9cd8eaca-6d2a-4567-961b-b15c2290fb56'
        url = reverse('task-terminate', args=[task_id])
        self.assertEqual(url, '/api/tasks/{0}'.format(task_id))
