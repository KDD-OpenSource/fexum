from django.conf.urls import url
from tasks.views import TaskListView, TaskTerminateView


urlpatterns = [
    url(r'tasks$', TaskListView.as_view(), name='task-list'),
    url(r'tasks/(?P<task_id>[a-zA-Z0-9-]+)$', TaskTerminateView.as_view(), name='task-terminate')
]