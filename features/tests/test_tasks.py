from os import stat
from time import time
from unittest.mock import patch, call

import SharedArray as sa
from django.test import TestCase

from features.models import Feature, Sample, Bin, Dataset, Slice, Redundancy, Relevancy, \
    Spectrogram
from features.models import ResultCalculationMap, Calculation
from features.tasks import _dataframe_columns, _dataframe_last_access, _get_dataframe
from features.tasks import initialize_from_dataset, build_histogram, downsample_feature, \
    calculate_feature_statistics, calculate_hics, calculate_densities, remove_unused_dataframes, \
    build_spectrogram
from features.tests.factories import FeatureFactory, DatasetFactory, ResultCalculationMapFactory, CalculationFactory


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
        feature = Feature.objects.get(dataset=dataset, name='Col2')

        bin_values = [6, 1, 4, 0, 2]
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
        feature = Feature.objects.get(dataset=dataset, name='Col2')
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
            self.assertGreater(y, 0.15)
            self.assertLess(y, 0.6)


class TestDownsampleTask(TestCase):
    def test_downsample_feature(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col2')

        sample_count = 5
        downsample_feature(feature_id=feature.id, sample_count=sample_count)

        samples = Sample.objects.filter(feature=feature)

        # Test that samples get created from 10 datapoints
        self.assertEqual(samples.count(), sample_count)
        self.assertEqual([sample.value for sample in samples],
                         [-0.426213735, -0.37090778, 0.097019415, -0.48668665, -0.178641])


class TestCalculateFeatureStatistics(TestCase):
    def test_calculate_feature_statistics(self):
        dataset = _build_test_dataset()
        feature = Feature.objects.get(dataset=dataset, name='Col2')

        calculate_feature_statistics(feature_id=feature.id)

        feature = Feature.objects.get(id=feature.id)

        self.assertEqual(feature.mean, -0.2838365385)
        self.assertEqual(feature.variance, 0.406014248150876)
        self.assertEqual(feature.min, -1.3975821)
        self.assertEqual(feature.max, 0.74163977)
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
        self.assertEqual(feature.categories, [0, 1, 2])
        self.assertEqual(feature.is_categorical, True)


class TestCalculateHics(TestCase):
    def test_calculate_incremental_hics(self):
        pass

    def test_calculate_bivariate_hics(self):
        dataset = _build_test_dataset()
        feature1 = Feature.objects.get(dataset=dataset, name='Col1')
        feature2 = Feature.objects.get(dataset=dataset, name='Col2')
        target = Feature.objects.get(dataset=dataset, name='Col3')
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map, max_iteration=2, type=Calculation.DEFAULT_HICS)
        features = [feature1, feature2]

        # Select first feature as target
        calculate_hics(calculation_id=calculation.id, bivariate=True, calculate_redundancies=True)
        calculate_hics(calculation_id=calculation.id, bivariate=True, calculate_redundancies=True)

        # Result
        self.assertEqual(ResultCalculationMap.objects.count(), 1)

        # Relevancies
        for relevancy in Relevancy.objects.all():
            self.assertIsNotNone(relevancy.relevancy)
            self.assertEqual(relevancy.result_calculation_map.target, target)
            self.assertEqual(relevancy.iteration, 10) 
            self.assertIn(relevancy.features.first(), [feature1, feature2])
        self.assertEqual(Relevancy.objects.filter(features=feature1).count(), 1)
        self.assertEqual(Relevancy.objects.filter(features=feature2).count(), 1)

        # Slices
        for fslice in Slice.objects.all():
            self.assertNotEqual(fslice.object_definition, [])
            self.assertNotEqual(fslice.output_definition, [])
            self.assertEqual(fslice.result_calculation_map.target, target)
            self.assertIn(fslice.features.first(), features)
        self.assertEqual(Slice.objects.filter(features=feature1).count(), 1)
        self.assertEqual(Slice.objects.filter(features=feature2).count(), 1)

        # Redundancies
        self.assertEqual(Redundancy.objects.count(), 1)
        self.assertTrue((Redundancy.objects.first().first_feature == feature1 and Redundancy.objects.first().second_feature == feature2)
            or (Redundancy.objects.first().second_feature == feature1 and Redundancy.objects.first().first_feature == feature2))
        # self.assertEqual(Redundancy.objects.first().redundancy, 1)

        # Calculation
        calculation = Calculation.objects.filter(result_calculation_map=ResultCalculationMap.objects.get(target=target)).last()
        self.assertIsNotNone(calculation)
        self.assertEqual(calculation.current_iteration, calculation.max_iteration)
        self.assertEqual(calculation.type, Calculation.DEFAULT_HICS)

    def test_calculate_feature_set_hics(self):
        dataset = _build_test_dataset()
        feature1 = Feature.objects.get(dataset=dataset, name='Col1')
        feature2 = Feature.objects.get(dataset=dataset, name='Col2')
        target = Feature.objects.get(dataset=dataset, name='Col3')
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map, max_iteration=1, type=Calculation.FIXED_FEATURE_SET_HICS)
        features = [feature1, feature2]
        
        feature_ids = [feature1.id, feature2.id]
        calculate_hics(calculation_id=calculation.id, bivariate=False, feature_ids=feature_ids)

        # Relevancy
        relevancy_features = Relevancy.objects.filter(features=feature1)
        relevancy_features = relevancy_features.filter(features=feature2)
        self.assertEqual(relevancy_features.count(), Relevancy.objects.count())
        self.assertEqual(relevancy_features.count(), 1)
        self.assertEqual(relevancy_features.first().iteration, 5)
        self.assertEqual(relevancy_features.first().result_calculation_map.target, target)
        self.assertIsNotNone(relevancy_features.first().relevancy)

        for feature in relevancy_features.first().features.all():
            self.assertIn(feature, features)

        # Slices
        slices_features = Slice.objects.filter(features=feature1)
        slices_features = slices_features.filter(features=feature2)
        self.assertEqual(slices_features.count(), Slice.objects.count())
        self.assertEqual(slices_features.count(), 1)
        self.assertEqual(slices_features.first().result_calculation_map.target, target)
        self.assertNotEqual(slices_features.first().output_definition, [])
        self.assertNotEqual(slices_features.first().object_definition, [])

        # Calculation
        calculation = Calculation.objects.filter(result_calculation_map=ResultCalculationMap.objects.get(target=target)).last()
        self.assertIsNotNone(calculation)
        self.assertEqual(calculation.current_iteration, calculation.max_iteration)
        self.assertEqual(calculation.type, Calculation.FIXED_FEATURE_SET_HICS)

    def test_calculate_super_set_hics(self):
        dataset = _build_test_dataset()
        feature1 = Feature.objects.get(dataset=dataset, name='Col1')
        feature2 = Feature.objects.get(dataset=dataset, name='Col2')
        target = Feature.objects.get(dataset=dataset, name='Col3')
        result_calculation_map = ResultCalculationMapFactory(target=target)
        calculation = CalculationFactory(result_calculation_map=result_calculation_map, max_iteration=1, type=Calculation.FEATURE_SUPER_SET_HICS)

        feature_ids = [feature1.id]
        calculate_hics(calculation_id=calculation.id, bivariate=False, feature_ids=feature_ids, calculate_supersets=True)

        # Relevancy
        relevancy_supersets = Relevancy.objects.filter(features=feature1)
        self.assertEqual(relevancy_supersets.count(), Relevancy.objects.count())
        self.assertGreater(relevancy_supersets.count(), 0)

        iteration_sum = 0
        for relevancy in relevancy_supersets.all():
            iteration_sum += relevancy.iteration
            self.assertEqual(relevancy.result_calculation_map.target, target)
            self.assertIsNotNone(relevancy.relevancy)
        self.assertEqual(iteration_sum, 10)

        # Slices
        slices_supersets = Slice.objects.filter(features=feature1)
        self.assertEqual(slices_supersets.count(), Slice.objects.count())
        self.assertGreater(slices_supersets.count(), 0)

        for fslices in slices_supersets.all():
            self.assertEqual(fslices.result_calculation_map.target, target)
            self.assertNotEqual(fslices.output_definition, [])
            self.assertNotEqual(fslices.object_definition, [])

        # Calculation
        calculation = Calculation.objects.filter(result_calculation_map=ResultCalculationMap.objects.get(target=target)).last()
        self.assertIsNotNone(calculation)
        self.assertEqual(calculation.current_iteration, calculation.max_iteration)
        self.assertEqual(calculation.type, Calculation.FEATURE_SUPER_SET_HICS)


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
        self.assertEqual(stat(spectrogram.image.name).st_size, 699)


class TestCalculateArbitarySlices(TestCase):
    pass


class TestCalculateConditionalDistributions(TestCase):
    def test_calculate_conditional_distributions_categorical(self):
        pass

    def test_calculate_conditional_distributions_in_range(self):
        pass
