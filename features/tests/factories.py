from factory import DjangoModelFactory, Sequence, SubFactory
from features.models import Sample, Feature, Bin, Slice, Dataset, Experiment, Result, Redundancy, Relevancy
from factory.fuzzy import FuzzyFloat, FuzzyInteger, FuzzyText
from factory.django import FileField
from users.tests.factories import UserFactory


class DatasetFactory(DjangoModelFactory):
    class Meta:
        model = Dataset

    name = FuzzyText(suffix='.csv')
    content = FileField(from_path='features/tests/test_file.csv')
    status = Dataset.PROCESSING


class FeatureFactory(DjangoModelFactory):
    class Meta:
        model = Feature

    name = Sequence(lambda n: 'feature_{0}'.format(n))
    dataset = SubFactory(DatasetFactory)
    min = FuzzyFloat(0, 1)
    max = FuzzyFloat(0, 1)
    mean = FuzzyFloat(0, 1)
    variance = FuzzyFloat(0, 1)
    is_categorical = False


class ExperimentFactory(DjangoModelFactory):
    class Meta:
        model = Experiment

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
    order = Sequence(lambda n: n)


class ResultFactory(DjangoModelFactory):
    class Meta:
        model = Result

    target = SubFactory(FeatureFactory)


class RelevancyFactory(DjangoModelFactory):
    class Meta:
        model = Relevancy

    feature = SubFactory(FeatureFactory)
    relevancy = FuzzyFloat(0, 1)
    rank = FuzzyInteger(0, 100)
    rar_result = SubFactory(ResultFactory)


class RedundancyFactory(DjangoModelFactory):
    class Meta:
        model = Redundancy

    first_feature = SubFactory(FeatureFactory)
    redundancy = FuzzyFloat(0, 1)
    second_feature = SubFactory(FeatureFactory)
    weight = 1
    rar_result = SubFactory(ResultFactory)


class SliceFactory(DjangoModelFactory):
    class Meta:
        model = Slice

    relevancy = SubFactory(RelevancyFactory)
    from_value = FuzzyFloat(-200.0, 0)
    to_value = FuzzyFloat(0, 200)
    marginal_distribution = [0, 1, 0]
    conditional_distribution = [0, 1, 0]
    deviation = FuzzyFloat(0, 1)
    frequency = FuzzyFloat(0, 1)
