from django.test import TestCase
from django.urls import reverse


class TestExperimentListUrl(TestCase):
    def test_sexperiment_list_url(self):
        url = reverse('experiment-list')
        self.assertEqual(url, '/api/experiments')


class TestExperimentDetailUrl(TestCase):
    def test_experiment_detail_url(self):
        url = reverse('experiment-detail', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/experiments/391ec5ac-f741-45c9-855a-7615c89ce129')


class TestExperimentTargetsDetailUrl(TestCase):
    def test_experiment_targets_detail_url(self):
        url = reverse('experiment-targets-detail', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/experiments/391ec5ac-f741-45c9-855a-7615c89ce129/target')


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
        url = reverse('target-feature-slices', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/targets/391ec5ac-f741-45c9-855a-7615c89ce129/slices')


class TestTargetFeatureRelevancyResultsUrl(TestCase):
    def test_target_feature_relevancy_results_url(self):
        url = reverse('target-feature-relevancy_results',
                      args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url, '/api/targets/391ec5ac-f741-45c9-855a-7615c89ce129/relevancy_results')


class TestDatasetRedundancyResultsUrl(TestCase):
    def test_dataset_redundancy_results(self):
        url = reverse('feature-redundancy_results', args=['391ec5ac-f741-45c9-855a-7615c89ce129'])
        self.assertEqual(url,
                         '/api/targets/391ec5ac-f741-45c9-855a-7615c89ce129/redundancy_results')


class TestFeatureSpectrogramUrl(TestCase):
    def test_feature_spectrogram_url(self):
        url = reverse('feature-spectrogram', args=['391ec5ac-f741-45c9-855a-7615c89ce128'])
        self.assertEqual(url, '/api/features/391ec5ac-f741-45c9-855a-7615c89ce128/spectrogram')


class TestFixedFeatureSetHicsUrl(TestCase):
    def test_fixed_feature_set_hics(self):
        url = reverse('fixed-feature-set-hics', args=['391ec5ac-f741-45c9-855a-7615c89ce128'])
        self.assertEqual(url, '/api/targets/391ec5ac-f741-45c9-855a-7615c89ce128/hics')


class TestRetrieveCalculations(TestCase):
    def test_retrieve_calculations(self):
        url = reverse('calculation-list')
        self.assertEqual(url, '/api/calculations')


class TestCurrentExperimentView(TestCase):
    def test_retrieve_current_experiment(self):
        url = reverse('current-experiment-detail')
        self.assertEqual(url, '/api/experiments/current')


class TestSetCurrentExperimentView(TestCase):
    def test_set_current_experiment(self):
        url = reverse('set-current-experiment', args=['391ec5ac-f741-45c9-855a-7615c89ce128'])
        self.assertEqual(url, '/api/experiments/current/391ec5ac-f741-45c9-855a-7615c89ce128')
