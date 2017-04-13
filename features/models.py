from django.db import models
from jsonfield import JSONField
from django.conf import settings
from uuid import uuid4
from django.utils.timezone import now


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    content = models.FileField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PROCESSING) # TODO: Use status appriatly
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.name


class ResultCalculationMap(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(editable=False, default=now)  # TODO: Test
    target = models.ForeignKey('Feature', on_delete=models.CASCADE)


class Calculation(models.Model):
    EMPTY = 'empty'
    DONE = 'done'

    STATUS_CHOICES = (
        (EMPTY, 'Empty'),
        (DONE, 'Done')
    )

    NONE = 'none'
    DEFAULT_HICS = 'default_hics'
    FIXED_FEATURES_HICS = 'fixed_features_hics'
    FEATURE_SET_HICS = 'feature_set_hics'

    RESULT_TYPE = (
        (NONE, 'None'),
        (DEFAULT_HICS, 'Default HiCS'),
        (FIXED_FEATURES_HICS, 'HiCS with fixed features'),
        (FEATURE_SET_HICS, 'HiCS with feature set')
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=EMPTY)
    type = models.CharField(max_length=10, choices=RESULT_TYPE, default=EMPTY)


class Relevancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    relevancy = models.FloatField()
    features = models.ManyToManyField('Feature')
    result_calculation_map = models.ForeignKey(ResultCalculationMap, on_delete=models.CASCADE)
    iteration = models.IntegerField()


class Redundancy(models.Model):
    class Meta:
        unique_together = ('first_feature', 'second_feature', 'result_calculation_map')

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    result_calculation_map = models.ForeignKey(ResultCalculationMap, on_delete=models.CASCADE)
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

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    mean = models.FloatField(blank=True, null=True)
    variance = models.FloatField(blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)
    is_categorical = models.NullBooleanField()
    categories = JSONField(default=None, blank=True, null=True)


class Sample(models.Model):
    class Meta:
        ordering = ('order',)

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    value = models.FloatField()
    order = models.IntegerField()


class Bin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    # TODO: Make sure from_value < to_value
    from_value = models.FloatField()
    to_value = models.FloatField()
    count = models.IntegerField()


class Slice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    definition = JSONField(default=[])
    features = models.ManyToManyField('Feature')  # TODO: Consider ManyToMany trough for relation uniquess
    result_calculation_map = models.ForeignKey(ResultCalculationMap, on_delete=models.CASCADE)


class Spectrogram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    width = models.IntegerField()
    height = models.IntegerField()
    image = models.FileField()
