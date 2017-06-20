from factory import DjangoModelFactory, Sequence, SubFactory
from features.models import Feature, Bin, Slice, Dataset, Experiment, ResultCalculationMap, Redundancy, \
    Relevancy, Spectrogram, Calculation, CurrentExperiment
from factory.fuzzy import FuzzyFloat, FuzzyInteger, FuzzyText
from factory.django import FileField, ImageField
from users.tests.factories import UserFactory
from factory import post_generation


class DatasetFactory(DjangoModelFactory):
    class Meta:
        model = Dataset

    name = FuzzyText(suffix='.csv')
    content = FileField(from_path='features/tests/assets/test_file.csv')
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
    visibility_text_filter = FuzzyText(length=150)
    visibility_rank_filter = FuzzyInteger(low=1, high=10)
    visibility_exclude_filter = FuzzyText(length=150)

    @post_generation
    def analysis_selection(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for feature in extracted:
                self.analysis_selection.add(feature)

    @post_generation
    def visibility_blacklist(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for feature in extracted:
                self.visibility_blacklist.add(feature)


class BinFactory(DjangoModelFactory):
    class Meta:
        model = Bin

    feature = SubFactory(FeatureFactory)
    from_value = FuzzyFloat(-200.0, 0)
    to_value = FuzzyFloat(0, 200)
    count = FuzzyInteger(1, 1000)


class ResultCalculationMapFactory(DjangoModelFactory):
    class Meta:
        model = ResultCalculationMap
    target = SubFactory(FeatureFactory)


class RelevancyFactory(DjangoModelFactory):
    class Meta:
        model = Relevancy

    iteration = FuzzyInteger(1, 100)
    relevancy = FuzzyFloat(0, 1)
    result_calculation_map = SubFactory(ResultCalculationMapFactory)

    @post_generation
    def features(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for feature in extracted:
                self.features.add(feature)


class RedundancyFactory(DjangoModelFactory):
    class Meta:
        model = Redundancy

    first_feature = SubFactory(FeatureFactory)
    redundancy = FuzzyFloat(0, 1)
    second_feature = SubFactory(FeatureFactory)
    weight = 1
    result_calculation_map = SubFactory(ResultCalculationMapFactory)


class SliceFactory(DjangoModelFactory):
    class Meta:
        model = Slice

    object_definition = []
    output_definition = []
    result_calculation_map = SubFactory(ResultCalculationMapFactory)

    @post_generation
    def features(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for feature in extracted:
                self.features.add(feature)


class SpectrogramFactory(DjangoModelFactory):
    class Meta:
        model = Spectrogram

    feature = SubFactory(FeatureFactory)
    width = FuzzyInteger(100, 500)
    height = FuzzyInteger(100, 500)
    image = ImageField(from_path='features/tests/assets/test_image.png')


class CalculationFactory(DjangoModelFactory):
    class Meta:
        model = Calculation

    result_calculation_map = SubFactory(ResultCalculationMapFactory)


class CurrentExperimentFactory(DjangoModelFactory):
    class Meta:
        model = CurrentExperiment

    user = SubFactory(UserFactory)
    experiment = SubFactory(ExperimentFactory)