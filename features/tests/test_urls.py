from django.urls import reverse
from django.test import TestCase


class TestFeatureListUrl(TestCase):
    def test_feature_list_url(self):
        url = reverse('feature-list')
        self.assertEqual(url, '/api/features')


class TestFeatureSamplesUrl(TestCase):
    def test_feature_samples_url(self):
        url = reverse('feature-samples', args=['Feature_1'])
        self.assertEqual(url, '/api/features/Feature_1/samples')


class TestFeatureHistogramUrl(TestCase):
    def test_feature_histogram_url(self):
        url = reverse('feature-histogram', args=['Feature_1'])
        self.assertEqual(url, '/api/features/Feature_1/histogram')


class TestFeatureSlicesUrl(TestCase):
    def test_feature_slices_url(self):
        url = reverse('feature-slices', args=['Feature_1'])
        self.assertEqual(url, '/api/features/Feature_1/slices')


class TestTargetDetailUrl(TestCase):
    def test_target_detail_url(self):
        url = reverse('target-detail')
        self.assertEqual(url, '/api/features/target')


class TestDatasetListUrl(TestCase):
    def test_target_list_url(self):
        url = reverse('dataset-list')
        self.assertEqual(url, '/api/datasets')


class TestDatasetUploadUrl(TestCase):
    def test_target_uplaod_url(self):
        url = reverse('dataset-upload', args=['a_dataset'])
        self.assertEqual(url, '/api/datasets/upload/a_dataset')
