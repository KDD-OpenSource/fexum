from django.db import models
from jsonfield import JSONField
from django.conf import settings
import uuid
from django.utils.timezone import now


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.ForeignKey('Feature', on_delete=models.CASCADE, blank=True, null=True)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)


class Dataset(models.Model):
    PROCESSING = 'processing'
    DONE = 'done'
    ERROR = 'error'

    STATUS_CHOICES = (
        (PROCESSING, 'Processing'),
        (ERROR, 'Error'),
        (DONE, 'Done')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    content = models.FileField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PROCESSING) # TODO: Use status appriatly
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name


class RarResult(models.Model):
    EMPTY = 'empty'
    DONE = 'done'

    STATUS_CHOICES = (
        (EMPTY, 'Empty'),
        (DONE, 'Done')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(editable=False, default=now) # TODO: Test
    target = models.ForeignKey('Feature', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=EMPTY)

    # TODO: Validation: target.dataset = feature.dataset

    def __str__(self):
        return 'Result for target '.format(self.target.name)


class Relevancy(models.Model):
    class Meta:
        unique_together = ('features', 'rank', 'rar_result',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relevancy = models.FloatField()
    rank = models.IntegerField()
    feature_set = models.ManyToManyField('Feature')
    rar_result = models.ForeignKey('RarResult', on_delete=models.CASCADE)


class Redundancy(models.Model):
    class Meta:
        unique_together = ('first_feature', 'second_feature', 'rar_result')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rar_result = models.ForeignKey('RarResult', on_delete=models.CASCADE)
    first_feature = models.ForeignKey('Feature', on_delete=models.CASCADE,
                                      related_name='first_features')
    second_feature = models.ForeignKey('Feature', on_delete=models.CASCADE,
                                       related_name='second_features')
    redundancy = models.FloatField()
    weight = models.IntegerField()


class Feature(models.Model):
    class Meta:
        ordering = ('name', )
        unique_together = (('name', 'dataset'),)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    mean = models.FloatField(blank=True, null=True)
    variance = models.FloatField(blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)
    is_categorical = models.NullBooleanField()
    categories = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return '{0} in {1} dataset'.format(self.name, self.dataset)


# Dataset are not separated
class Sample(models.Model):
    class Meta:
        ordering = ('order',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    value = models.FloatField()
    order = models.IntegerField()


class Bin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    # TODO: Make sure from_value < to_value
    from_value = models.FloatField()
    to_value = models.FloatField()
    count = models.IntegerField()


class Slice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relevancy = models.ForeignKey(Relevancy, on_delete=models.CASCADE)
    from_value = models.FloatField()
    deviation = models.FloatField()
    frequency = models.FloatField()
    to_value = models.FloatField()
    marginal_distribution = JSONField(default=[])
    conditional_distribution = JSONField(default=[])


