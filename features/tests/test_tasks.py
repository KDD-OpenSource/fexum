from django.test import TestCase
from features.tasks import initialize_from_dataset, build_histogram, downsample_feature, \
    calculate_feature_statistics, calculate_rar
from features.models import Feature, Sample, Bin
import pandas as pd
import numpy as np
from decimal import Decimal


def build_test_file():
    test_file = 'test_file.csv'
    feature_names = ['Col1', 'Col2']
    data = np.array([[-0.69597425, -0.24040447],
                     [0.78175798, 0.24011319],
                     [-0.34861004, -1.33975821],
                     [0.77591563, -0.6162023],
                     [-1.24479339, 0.74163977],
                     [2.15539917, -0.35207171],
                     [0.42175655, -0.38909846],
                     [2.24539624, -1.20669404],
                     [-0.83270608, -0.04607436],
                     [0.46184216, 0.41361159]])
    df = pd.DataFrame(data, columns=feature_names)
    df.to_csv(test_file, index=False)

    return test_file, feature_names


class TestInitializeFromDatasetTask(TestCase):
    def test_initialize_from_dataset(self):
        test_file, feature_names = build_test_file()

        initialize_from_dataset(test_file)

        self.assertEqual(feature_names, [feature.name for feature in Feature.objects.all()])


class TestBuildHistogramTask(TestCase):
    def test_build_histogram(self):
        test_file, feature_names = build_test_file()
        feature_name = feature_names[0]
        feature = Feature.objects.create(name=feature_name)
        bin_values = [3, 1, 4, 0, 2]

        build_histogram(test_file, feature_name)

        # Rudementary check bins only for its values
        self.assertEqual(Bin.objects.count(), len(bin_values))
        for bin_obj in Bin.objects.all():
            self.assertEqual(bin_obj.feature, feature)
            self.assertIn(bin_obj.count, bin_values)


class TestDownsampleTask(TestCase):
    def test_downsample_feature(self):
        test_file, feature_names = build_test_file()
        feature_name = feature_names[0]
        feature = Feature.objects.create(name=feature_name)

        sample_count = 5
        downsample_feature(test_file, feature_name, sample_count)

        samples = Sample.objects.filter(feature=feature)

        # Test that samples get created from 10 datapoints
        self.assertEqual(samples.count(), sample_count)
        self.assertEqual([sample.value for sample in samples],
                         [-0.69597425, -0.34861004, -1.24479339, 0.42175655, -0.83270608])


class TestCalculateFeatureStatistics(TestCase):
    def test_calculate_feature_statistics(self):
        test_file, feature_names = build_test_file()
        feature_name = feature_names[0]
        Feature.objects.create(name=feature_name)

        calculate_feature_statistics(test_file, feature_name)

        feature = Feature.objects.get(name=feature_name)

        self.assertEqual(feature.mean, 0.371998397)
        self.assertEqual(feature.variance, 1.2756908271439)
        self.assertEqual(feature.min, -1.24479339)
        self.assertEqual(feature.max, 2.24539624)


class TestCalculateRar(TestCase):
    def test_calculate_rar(self):
        test_file, feature_names = build_test_file()
        feature_name1 = feature_names[0]
        feature_name2 = feature_names[1]

        # Create two test features
        Feature.objects.create(name=feature_name1)
        Feature.objects.create(name=feature_name2)

        # Select first feature as target
        calculate_rar(test_file)

        # First feature aka the target should have no info
        feature1 = Feature.objects.get(name=feature_name1)
        self.assertIsNotNone(feature1.relevancy)
        self.assertIsNone(feature1.redundancy)

        # Should have info
        feature2 = Feature.objects.get(name=feature_name2)
        self.assertIsNone(feature2.relevancy)
        self.assertIsNone(feature2.redundancy)
