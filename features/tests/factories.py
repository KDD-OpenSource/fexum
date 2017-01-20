from factory import DjangoModelFactory, Sequence, SubFactory
from features.models import Sample, Feature, Bin, Slice, Dataset, Session, RarResult
from factory.fuzzy import FuzzyFloat, FuzzyInteger, FuzzyText
from factory.django import FileField
from django.conf import settings


class UserFactory(DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL


class DatasetFactory(DjangoModelFactory):
    class Meta:
        model = Dataset

    name = FuzzyText(suffix='.csv')
    content = FileField(from_path='features/tests/test_file.csv')


class FeatureFactory(DjangoModelFactory):
    class Meta:
        model = Feature

    name = Sequence(lambda n: 'feature_{0}'.format(n))
    dataset = SubFactory(DatasetFactory)
    min = FuzzyFloat(0, 1)
    max = FuzzyFloat(0, 1)
    mean = FuzzyFloat(0, 1)
    variance = FuzzyFloat(0, 1)


class SessionFactory(DjangoModelFactory):
    class Meta:
        model = Session

    user = SubFactory(UserFactory)
    dataset = SubFactory(DatasetFactory)
    target = SubFactory(FeatureFactory)


class BinFactory(DjangoModelFactory):
    class Meta:
        model = Bin

    feature = SubFactory(FeatureFactory)
    from_value = FuzzyFloat(-200.0, 0)
    to_value = FuzzyFloat(0, 200)
    count = FuzzyInteger(1, 1000)


class SampleFactory(DjangoModelFactory):
    class Meta:
        model = Sample

    feature = SubFactory(FeatureFactory)
    value = FuzzyFloat(0, 200)


class RarResultFactory(DjangoModelFactory):
    class Meta:
        model = RarResult

    feature = SubFactory(FeatureFactory)
    relevancy = FuzzyFloat(0, 200)
    redundancy = FuzzyFloat(0, 200)
    rank = FuzzyInteger(0, 100)
    target = SubFactory(FeatureFactory)


class SliceFactory(DjangoModelFactory):
    class Meta:
        model = Slice

    rar_result = SubFactory(RarResultFactory)
    from_value = FuzzyFloat(-200.0, 0)
    to_value = FuzzyFloat(0, 200)
    marginal_distribution = [0, 1, 0]
    conditional_distribution = [0, 1, 0]
    deviation = FuzzyFloat(0, 1)
    frequency = FuzzyFloat(0, 1)
    significance = FuzzyFloat(0, 1)
