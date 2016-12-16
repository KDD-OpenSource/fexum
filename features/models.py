from django.db import models
from jsonfield import JSONField


class Feature(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    relevancy = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    redundancy = models.DecimalField(max_digits=6, decimal_places=5, blank=True, null=True)
    rank = models.IntegerField(unique=True, blank=True, null=True)
    is_target = models.BooleanField(default=False) # Never use directly

    def select_as_target(self):
        # TODO: Fix that no target is selected if validation for self failed
        Feature.objects.all().update(is_target=False)
        self.is_target = True


class Histogram(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)


class Bucket(models.Model):
    histogram = models.ForeignKey(Histogram, on_delete=models.CASCADE)
    # TODO: Make sure from_value < to_value
    from_value = models.DecimalField(max_digits=10, decimal_places=5)
    to_value = models.DecimalField(max_digits=10, decimal_places=5)
    count = models.IntegerField()


class Slice(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    from_value = models.DecimalField(max_digits=10, decimal_places=5)
    to_value = models.DecimalField(max_digits=10, decimal_places=5)
    marginal_distribution = JSONField(default=[])
    conditional_distribution = JSONField(default=[])
