from django.urls import reverse
from django.test import TestCase


class TestSessionListUrl(TestCase):
    def test_session_list_url(self):
        url = reverse('session-list')
        self.assertEqual(url, '/api/sessions')


class TestSessionListUrl(TestCase):
    def test_session_detail_url(self):
        url = reverse('session-detail', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/sessions/391ec5ac-f741-45c9-855a-7615c89ce129')


class TestSessionTargetsDetailUrl(TestCase):
    def test_session_targets_detail_url(self):
        url = reverse('session-targets-detail', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/sessions/391ec5ac-f741-45c9-855a-7615c89ce129/target')


class TestDatasetListView(TestCase):
    def test_dataset_list_url(self):
        url = reverse('dataset-list')
        self.assertEqual(url, '/api/datasets')


class TestDatasetUploadUrl(TestCase):
    def test_target_upload_url(self):
        url = reverse('dataset-upload')
        self.assertEqual(url, '/api/datasets/upload')


class TestDatasetFeaturesListUrl(TestCase):
    def test_feature_list_url(self):
        url = reverse('dataset-features-list', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/datasets/391ec5ac-f741-45c9-855a-7615c89ce129/features')


class TestFeatureSamplesUrl(TestCase):
    def test_feature_samples_url(self):
        url = reverse('feature-samples', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/features/391ec5ac-f741-45c9-855a-7615c89ce129/samples')


class TestFeatureHistogramUrl(TestCase):
    def test_feature_histogram_url(self):
        url = reverse('feature-histogram', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/features/391ec5ac-f741-45c9-855a-7615c89ce129/histogram')


class TestFeatureSlicesUrl(TestCase):
    def test_feature_slices_url(self):
        url = reverse('session-feature-slices', args=['391ec5ac-f741-45c9-855a-7615c89ce129',
                                                       '391ec5ac-f741-45c9-855a-7615c89ce128'])
        self.assertEqual(url,'/api/sessions/391ec5ac-f741-45c9-855a-7615c89ce129/' +
                         'features/391ec5ac-f741-45c9-855a-7615c89ce128/slices')


class TestSessionFeatureRarResultsUrl(TestCase):
    def test_session_feature_rar_results_url(self):
        url = reverse('session-feature-rar_results', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/sessions/391ec5ac-f741-45c9-855a-7615c89ce129/rar_results')
