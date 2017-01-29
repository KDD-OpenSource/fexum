from django.db import models
from jsonfield import JSONField
from django.conf import settings
import uuid


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.ForeignKey('Feature', on_delete=models.CASCADE, blank=True, null=True)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)


class Dataset(models.Model):
    EMPTY = 'empty'
    PROCESSING = 'processing'
    IN_MEMORY = 'in_memory'
    ON_DISK = 'on_disk'
    ERROR = 'error'

    STATUS_CHOICES = (
        (EMPTY, 'Empty'),
        (PROCESSING, 'Processing'),
        (IN_MEMORY, 'In Memory'),
        (ON_DISK, 'ON Disk'),
        (ERROR, 'Error')
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    content = models.FileField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=EMPTY)

    def __str__(self):
        return self.name


class RelevancyResult(models.Model):
    class Meta:
        unique_together = ('target', 'feature', 'rank')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relevancy = models.FloatField()
    rank = models.IntegerField()
    target = models.ForeignKey('Feature', on_delete=models.CASCADE,
                               related_name='target_rar_results')
    feature = models.ForeignKey('Feature', on_delete=models.CASCADE)

    # TODO: Validation: target.dataset = feature.dataset

    def __str__(self):
        try:
            return 'Relevancy of {0} for target {1}'.format(self.feature, self.target)
        except:
            return 'Processing…'


class RedundancyResult(models.Model):
    class Meta:
        unique_together = ('first_feature', 'second_feature')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_feature = models.ForeignKey('Feature', on_delete=models.CASCADE,
                                      related_name='first_features')
    second_feature = models.ForeignKey('Feature', on_delete=models.CASCADE,
                                       related_name='second_features')
    redundancy = models.FloatField()
    weight = models.IntegerField()

    # TODO: Validate first_feture.dataset = second_feature.dataset

    def __str__(self):
        try:
            return 'Redundancy of {0} and {1}'.format(self.first_feature, self.second_feature)
        except:
            return 'Processing…'


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
    
    def __str__(self):
        return '{0} in {1} dataset'.format(self.name, self.dataset)


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
    relevancy_result = models.ForeignKey(RelevancyResult, on_delete=models.CASCADE)
    from_value = models.FloatField()
    deviation = models.FloatField()
    frequency = models.FloatField()
    to_value = models.FloatField()
    marginal_distribution = JSONField(default=[])
    conditional_distribution = JSONField(default=[])


