from celery.task.control import inspect, revoke
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT


def _get_tasks():
    tasks = inspect()
    scheduled_tasks = tasks.scheduled() or {}
    active_tasks = tasks.active() or {}
    reserved_tasks = tasks.reserved() or {}

    result = {
        'scheduled': scheduled_tasks,
        'active': active_tasks,
        'reserved': reserved_tasks
    }
    return result


class TaskListView(APIView):
    def get(self, _):
        tasks = _get_tasks()
        return Response(tasks)


class TaskTerminateView(APIView):
    def delete(self, _, task_id):
        revoke(task_id, terminate=True)
        return Response(status=HTTP_204_NO_CONTENT)
