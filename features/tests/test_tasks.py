from django.test import TestCase
from features.tasks import initialize_from_dataset, build_histogram, downsample_feature, \
    calculate_feature_statistics, calculate_rar
from features.models import Feature, Sample, Bin, Dataset, RarResult, Slice
from features.tests.factories import FeatureFactory, DatasetFactory


def _build_test_dataset() -> Dataset:
    dataset = DatasetFactory()
    feature_names = ['Col1', 'Col2']
    for feature_name in feature_names:
        FeatureFactory(name=feature_name, dataset=dataset)

    return dataset


class TestInitializeFromDatasetTask(TestCase):
    def test_initialize_from_dataset(self):
        dataset = DatasetFactory()
        feature_names = ['Col1', 'Col2']

        initialize_from_dataset(dataset_id=dataset.id)

        self.assertEqual(feature_names, [feature.name for feature in Feature.objects.all()])


class TestBuildHistogramTask(TestCase):
    def test_build_histogram(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')

        bin_values = [3, 1, 4, 0, 2]

        build_histogram(feature_id=feature.id)

        # Rudementary check bins only for its values
        self.assertEqual(Bin.objects.count(), len(bin_values))
        for bin_obj in Bin.objects.all():
            self.assertEqual(bin_obj.feature, feature)
            self.assertIn(bin_obj.count, bin_values)


class TestDownsampleTask(TestCase):
    def test_downsample_feature(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')

        sample_count = 5
        downsample_feature(feature_id=feature.id, sample_count=sample_count)

        samples = Sample.objects.filter(feature=feature)

        # Test that samples get created from 10 datapoints
        self.assertEqual(samples.count(), sample_count)
        self.assertEqual([sample.value for sample in samples],
                         [-0.69597425, -0.34861004, -1.24479339, 0.42175655, -0.83270608])


class TestCalculateFeatureStatistics(TestCase):
    def test_calculate_feature_statistics(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')

        calculate_feature_statistics(feature_id=feature.id)

        feature = Feature.objects.get(id=feature.id)

        self.assertEqual(feature.mean, 0.371998397)
        self.assertEqual(feature.variance, 1.2756908271439)
        self.assertEqual(feature.min, -1.24479339)
        self.assertEqual(feature.max, 2.24539624)


class TestCalculateRar(TestCase):
    def test_calculate_rar(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')
        target = Feature.objects.get(dataset=dataset, name='Col2')

        # Select first feature as target
        calculate_rar(target_id=target.id)

        self.assertEqual(RarResult.objects.count(), 1,
                         msg='Should only contain result for the one feature')
        rar_result = RarResult.objects.first()

        self.assertIsNotNone(rar_result.relevancy)
        self.assertIsNone(rar_result.redundancy)
        self.assertIsNotNone(rar_result.rank)
        self.assertEqual(rar_result.target, target)
        self.assertEqual(rar_result.feature, feature)
        self.assertEqual(Slice.objects.filter(rar_result=rar_result).count(), 6)
