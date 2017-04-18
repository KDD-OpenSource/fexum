from django.test import TestCase
from features.tasks import initialize_from_dataset, build_histogram, downsample_feature, \
    calculate_feature_statistics, calculate_hics, calculate_densities, remove_unused_dataframes, \
    build_spectrogram
from features.models import Feature, Sample, Bin, Dataset, Slice, Redundancy, Relevancy, \
    ResultCalculationMap, Spectrogram
from features.tests.factories import FeatureFactory, DatasetFactory, ResultCalculationMapFactory
from unittest.mock import patch, call
from time import time
import SharedArray as sa
from features.tasks import _dataframe_columns, _dataframe_last_access, _get_dataframe
from os import stat


# TODO: test for results
def _build_test_dataset() -> Dataset:
    dataset = DatasetFactory()
    feature_names = ['Col1', 'Col2', 'Col3']
    for feature_name in feature_names:
        FeatureFactory(name=feature_name, dataset=dataset)

    return dataset


class TestInitializeFromDatasetTask(TestCase):
    def test_initialize_from_dataset(self):
        dataset = DatasetFactory()
        feature_names = ['Col1', 'Col2', 'Col3']

        # TODO: Fuck nesting
        with patch('features.tasks.build_histogram.subtask') as build_histogram_mock:
            with patch('features.tasks.downsample_feature.subtask') as downsample_feature_mock:
                with patch('features.tasks.calculate_feature_statistics.subtask') \
                        as calculate_feature_statistics_mock:
                    with patch('features.tasks.build_spectrogram.subtask') \
                            as build_spectrogram_mock:
                        with patch('features.tasks.initialize_from_dataset_processing_callback.subtask') \
                                as initialize_from_dataset_processing_callback_mock:
                            with patch('features.tasks.chord') \
                                    as chord_mock:

                                initialize_from_dataset(dataset_id=dataset.id)

                                # Make sure that we call the preprocessing task for each feature
                                features = Feature.objects.filter(name__in=feature_names).all()
                                kalls = [call(immutable=True, kwargs={'feature_id': feature.id}) for feature in features]

                                build_histogram_mock.assert_has_calls(kalls, any_order=True)
                                calculate_feature_statistics_mock.assert_has_calls(kalls, any_order=True)
                                downsample_feature_mock.assert_has_calls(kalls, any_order=True)
                                build_spectrogram_mock.assert_has_calls(kalls, any_order=True)

                                initialize_from_dataset_processing_callback_mock.assert_called_once_with(
                                    kwargs={'dataset_id': dataset.id})
                                chord_mock.assert_called_once()

        self.assertEqual(feature_names, [feature.name for feature in Feature.objects.all()])


class TestBuildHistogramTask(TestCase):
    def test_build_histogram(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')

        bin_values = [3, 1, 4, 0, 2]
        bin_count = len(bin_values)

        build_histogram(feature_id=feature.id, bins=bin_count)

        # Rudementary check bins only for its values
        self.assertEqual(Bin.objects.count(), bin_count)
        for bin_obj in Bin.objects.all():
            self.assertEqual(bin_obj.feature, feature)
            self.assertIn(bin_obj.count, bin_values)


class TestCalculateDensities(TestCase):
    def test_calculate_densities(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')
        target_feature = Feature.objects.get(dataset=dataset, name='Col3')

        target_feature.categories = [0, 1, 2]
        target_feature.save()
        count_categories = len(target_feature.categories)
        validation_category = 1.0

        densities = calculate_densities(str(target_feature.id), str(feature.id))

        self.assertIsInstance(densities, list)
        self.assertEqual(len(densities), count_categories)
        self.assertIn(validation_category, (d['target_class'] for d in densities))
        validation_category_density = next(d for d in densities if d['target_class'] == validation_category)
        validation_category_density_values = validation_category_density['density_values']

        # Kernel density is not deterministic, therefore we only check result length and valid range
        self.assertEqual(len(validation_category_density_values), 100)
        for y in validation_category_density_values:
            self.assertGreater(y, 0.2)
            self.assertLess(y, 0.3)


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
                         [0.042891865, 0.213652795, 0.45530289, 1.333576395, -0.18543196])


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
        self.assertEqual(feature.is_categorical, False)
        self.assertEqual(feature.categories, None)

    def test_calculate_feature_statistics_is_categorical(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col3')

        calculate_feature_statistics(feature_id=feature.id)

        feature = Feature.objects.get(id=feature.id)

        self.assertEqual(feature.mean, 0.9)
        self.assertEqual(feature.variance, 0.69)
        self.assertEqual(feature.min, 0)
        self.assertEqual(feature.max, 2.0)
        self.assertEqual(feature.is_categorical, True)
        self.assertEqual(feature.categories, [0, 1, 2])


class TestCalculateHics(TestCase):
    def test_calculate_incremental_hics(self):
        pass

    def test_calculate_hics(self):
        dataset = _build_test_dataset()
        feature1 = Feature.objects.get(dataset=dataset, name='Col1')
        feature2 = Feature.objects.get(dataset=dataset, name='Col2')
        target = Feature.objects.get(dataset=dataset, name='Col3')

        # Select first feature as target
        calculate_hics(target_id=target.id)

        self.assertEqual(Result.objects.count(), 1)

        # Relevancies
        self.assertEqual(Relevancy.objects.count(), 2,
                         msg='Should only contain relevancy for the one feature')
        for relevancy in Relevancy.objects.all():
            self.assertIsNotNone(relevancy.relevancy)
            self.assertIsNotNone(relevancy.rank)
            self.assertEqual(relevancy.rar_result.target, target)
            assert relevancy.feature == feature1 or relevancy.feature == feature2
            self.assertEqual(Slice.objects.filter(relevancy=relevancy).count(), 6)

        # Redundancies
        self.assertEqual(Redundancy.objects.count(), 1,
                         msg='Should only contain redundancy for one feature pair')

        redundancy = Redundancy.objects.first()
        self.assertIsNotNone(redundancy.redundancy)
        assert redundancy.first_feature == feature1 or redundancy.first_feature == feature2
        assert redundancy.second_feature == feature1 or redundancy.second_feature == feature2

    def test_calculate_hics_catch_if_already_calcalulated_for_target(self):
        dataset = _build_test_dataset()
        target = Feature.objects.get(dataset=dataset, name='Col2')

        # Init a typical result configuration
        rar_result = ResultFactory(target=target)
        self.assertEqual(Result.objects.count(), 1,
                         msg='Should only contain result for the one feature')

        # Signals are called manually
        with patch('features.tasks.pre_save.send') as pre_save_signal_mock:
            with patch('features.tasks.post_save.send') as post_save_signal_mock:
                calculate_hics(target_id=target.id)

                post_save_signal_mock.assert_called_once_with(Result, created=False,
                                                              instance=rar_result)
                pre_save_signal_mock.assert_called_once_with(Result, instance=rar_result)

        self.assertEqual(Result.objects.count(), 1,
                         msg='Should still only contain result for the one feature')

    def test_calculate_hics_use_precalulated_data(self):
        # TODO: Write test
        pass


class TestRemoveUnusedDatasets(TestCase):
    def test_remove_unused_datasets(self):
        dataset = _build_test_dataset()

        # Manually load the dataframe into memory
        _get_dataframe(dataset.id)

        self.assertLess(_dataframe_last_access[str(dataset.id)], time())
        self.assertGreater(_dataframe_last_access[str(dataset.id)], time() - 60)
        self.assertEqual(list(_dataframe_columns[str(dataset.id)]), [feature.name for feature in dataset.feature_set.all()])
        self.assertIn(str(dataset.id), [dataset.name.decode('ascii') for dataset in sa.list()])

        remove_unused_dataframes(max_delta=0)

        self.assertNotIn(str(dataset.id), _dataframe_last_access)
        self.assertNotIn(str(dataset.id), _dataframe_columns)
        self.assertNotIn(str(dataset.id), [dataset.name.decode('ascii') for dataset in sa.list()])

 
class TestBuildSpectrogram(TestCase):
    def test_build_spectrogram(self):
        width = 10
        height = 34
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col1')

        build_spectrogram(feature.id, height=height, width=width)

        spectrogram = Spectrogram.objects.get(feature=feature)

        self.assertEqual(spectrogram.feature, feature)
        self.assertEqual(spectrogram.width, width)
        self.assertEqual(spectrogram.height, height)
        self.assertEqual(stat(spectrogram.image.name).st_size, 610)


class TestCalculateArbitarySlices(TestCase):
    pass


class TestCalculateConditionalDistributions(TestCase):
    def test_calculate_conditional_distributions_categorical(self):
        pass

    def test_calculate_conditional_distributions_in_range(self):
        pass
