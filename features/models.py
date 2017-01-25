from django.db import models
from jsonfield import JSONField
from django.conf import settings
import uuid


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target = models.ForeignKey('Feature', on_delete=models.CASCADE, blank=True, null=True)
    dataset = models.ForeignKey('Dataset', on_delete=models.CASCADE)


class Dataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    content = models.FileField()

    def __str__(self):
        return self.name


class RarResult(models.Model):
    class Meta:
        unique_together = ('target', 'feature', 'rank')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    relevancy = models.FloatField()
    redundancy = models.FloatField(blank=True, null=True)
    rank = models.IntegerField()
    target = models.ForeignKey('Feature', on_delete=models.CASCADE,
                               related_name='target_rar_results')
    feature = models.ForeignKey('Feature', on_delete=models.CASCADE)
    # TODO: Validation: target.dataset = feature.dataset

    def __str__(self):
        try:
            return '{0} for target {1}'.format(self.feature, self.target)
        except:
            return 'Processing…'


class Feature(models.Model):
    class Meta:
        unique_together = (('name', 'dataset'),)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    mean = models.FloatField(blank=True, null=True)
    variance = models.FloatField(blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return '{0} in {1} dataset'.format(self.name, self.dataset)


class Sample(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    value = models.FloatField()


class Bin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    # TODO: Make sure from_value < to_value
    from_value = models.FloatField()
    to_value = models.FloatField()
    count = models.IntegerField()


class Slice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rar_result = models.ForeignKey(RarResult, on_delete=models.CASCADE)
    from_value = models.FloatField()
    deviation = models.FloatField()
    significance = models.FloatField()
    frequency = models.FloatField()
    to_value = models.FloatField()
    marginal_distribution = JSONField(default=[])
    conditional_distribution = JSONField(default=[])
