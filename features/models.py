from django.db import models
from jsonfield import JSONField


class Feature(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False, unique=True)
    relevancy = models.FloatField(blank=True, null=True)
    redundancy = models.FloatField(blank=True, null=True)
    rank = models.IntegerField(unique=True, blank=True, null=True)
    mean = models.FloatField(blank=True, null=True)
    variance = models.FloatField(blank=True, null=True)
    min = models.FloatField(blank=True, null=True)
    max = models.FloatField(blank=True, null=True)


class Target(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(Target, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()


class Sample(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    value = models.FloatField()


class Bin(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    # TODO: Make sure from_value < to_value
    from_value = models.FloatField()
    to_value = models.FloatField()
    count = models.IntegerField()


class Slice(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    from_value = models.FloatField()
    deviation = models.FloatField()
    significance = models.FloatField()
    frequency = models.FloatField()
    to_value = models.FloatField()
    marginal_distribution = JSONField(default=[])
    conditional_distribution = JSONField(default=[])
