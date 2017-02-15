from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from features.models import Dataset


@receiver(post_delete, sender=Dataset)
def dataset_delete(sender, instance, **kwargs):
    instance.content.delete(False)
