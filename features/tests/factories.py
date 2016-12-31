from factory import DjangoModelFactory, Sequence, SubFactory
from features.models import Sample, Feature, Bin, Histogram, Slice, Target
from factory.fuzzy import FuzzyDecimal, FuzzyInteger


class FeatureFactory(DjangoModelFactory):
    class Meta:
        model = Feature

    name = Sequence(lambda n: 'feature_{0}'.format(n))


class TargetFactory(DjangoModelFactory):
    class Meta:
        model = Target

    feature = SubFactory(FeatureFactory)


class HistogramFactory(DjangoModelFactory):
    class Meta:
        model = Histogram

    feature = SubFactory(FeatureFactory)


class BinFactory(DjangoModelFactory):
    class Meta:
        model = Bin

    histogram = SubFactory(HistogramFactory)
    from_value = FuzzyDecimal(-200.0, 0)
    to_value = FuzzyDecimal(0, 200)
    count = FuzzyInteger(1, 1000)


class SliceFactory(DjangoModelFactory):
    class Meta:
        model = Slice

    feature = SubFactory(FeatureFactory)
    from_value = FuzzyDecimal(-200.0, 0)
    to_value = FuzzyDecimal(0, 200)
    marginal_distribution = [0, 1, 0]
    conditional_distribution = [0, 1, 0]


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample

    feature = SubFactory(FeatureFactory)
    value = FuzzyDecimal(0, 200)
