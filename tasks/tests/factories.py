from celery import shared_task


@shared_task
def task_factory():
    return True  # Do nothing
