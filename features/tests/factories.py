from factory import DjangoModelFactory, Sequence
from features.models import Feature


class FeatureFactory(DjangoModelFactory):
    class Meta:
        model = Feature

    name = Sequence(lambda n: 'feature_{0}'.format(n))
