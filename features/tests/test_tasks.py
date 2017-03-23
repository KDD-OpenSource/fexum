from django.test import TestCase
from features.tasks import initialize_from_dataset, build_histogram, downsample_feature, \
    calculate_feature_statistics, calculate_hics
from features.models import Feature, Sample, Bin, Dataset, Slice, Redundancy, Relevancy, \
    Result
from features.tests.factories import FeatureFactory, DatasetFactory, RelevancyFactory, \
    RedundancyFactory, ResultFactory
from unittest.mock import patch, call

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
                    with patch('features.tasks.initialize_from_dataset_processing_callback.subtask') \
                            as initialize_from_dataset_processing_callback_mock:
                        with patch('features.tasks.chord') \
                                as chord_mock:

                            initialize_from_dataset(dataset_id=dataset.id)

                            # Make sure that we call the preprocessing task for each feature
                            features = Feature.objects.filter(name__in=feature_names).all()
                            kalls = [call(kwargs={'feature_id': feature.id}) for feature in features]

                            build_histogram_mock.assert_has_calls(kalls, any_order=True)
                            calculate_feature_statistics_mock.assert_has_calls(kalls, any_order=True)
                            downsample_feature_mock.assert_has_calls(kalls, any_order=True)
                            initialize_from_dataset_processing_callback_mock.assert_called_once_with(
                                kwargs={'dataset_id': dataset.id})
                            chord_mock.assert_called_once()

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

    def test_calculate_rar_use_precalulated_data(self):
        # TODO: Write test
        pass


class TestCalculateArbitarySlices(TestCase):
    pass


class TestCalculateConditionalDistributions(TestCase):
    def test_calculate_conditional_distributions_categorical(self):
        pass

    def test_calculate_conditional_distributions_in_range(self):
        pass