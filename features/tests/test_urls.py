from django.urls import reverse
from django.test import TestCase


class TestFeatureListUrl(TestCase):
    def test_feature_list_url(self):
        url = reverse('feature-list')
        self.assertEqual(url, '/features')


class TestTargetSelectUrl(TestCase):
    def test_target_select_url(self):
        url = reverse('target-select')
        self.assertEqual(url, '/features/target')


class TestFeatureSamplesUrl(TestCase):
    def test_feature_samples_url(self):
        url = reverse('feature-samples', args=['Feature_1'])
        self.assertEqual(url, '/features/Feature_1/samples')


class TestFeatureHistogramUrl(TestCase):
    def test_feature_histogram_url(self):
        url = reverse('feature-histogram', args=['Feature_1'])
        self.assertEqual(url, '/features/Feature_1/histogram')


class TestFeatureSlicesUrl(TestCase):
    def test_feature_slices_url(self):
        url = reverse('feature-slices', args=['Feature_1'])
        self.assertEqual(url, '/features/Feature_1/slices')
