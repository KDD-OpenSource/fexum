from django.conf.urls import url

from features.views import FeatureListView, FeatureSamplesView, DatasetListView, \
    FeatureHistogramView, FeatureSlicesView, TargetDetailView, DatasetViewUploadView, \
    ExperimentListView, FeatureRelevancyResultsView, ExperimentDetailView, TargetRedundancyResults, \
    ConditionalDistributionsView, FeatureDensityView, FeatureSpectrogramView, FixedFeatureSetHicsView, \
    CalculationListView, CurrentExperimentView, SetCurrentExperimentView

urlpatterns = [
    # Experiments
    url(r'experiments$', ExperimentListView.as_view(), name='experiment-list'),
    url(r'experiments/current$', CurrentExperimentView.as_view(), name='current-experiment-detail'),
    url(r'experiments/current/(?P<experiment_id>[a-zA-Z0-9-]+)$', SetCurrentExperimentView.as_view(),
        name='set-current-experiment'),
    url(r'experiments/(?P<experiment_id>[a-zA-Z0-9-]+)$', ExperimentDetailView.as_view(),
        name='experiment-detail'),
    url(r'experiments/(?P<experiment_id>[a-zA-Z0-9-]+)/target$', TargetDetailView.as_view(),
        name='experiment-targets-detail'),

    # Datasets
    url(r'datasets$', DatasetListView.as_view(), name='dataset-list'),
    url(r'datasets/upload$', DatasetViewUploadView.as_view(), name='dataset-upload'),
    url(r'datasets/(?P<dataset_id>[a-zA-Z0-9-]+)/features$', FeatureListView.as_view(),
        name='dataset-features-list'),

    # Features
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/samples(?:/(?P<max_samples>[0-9]+))?$', FeatureSamplesView.as_view(),
        name='feature-samples'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/spectrogram', FeatureSpectrogramView.as_view(),
        name='feature-spectrogram'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/histogram$', FeatureHistogramView.as_view(),
        name='feature-histogram'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/density/(?P<target_id>[a-zA-Z0-9-]+)$',
        FeatureDensityView.as_view(), name='feature-density'),

    # Results
    url(r'targets/(?P<target_id>[a-zA-Z0-9-]+)/slices$',
        FeatureSlicesView.as_view(), name='target-feature-slices'),
    url(r'targets/(?P<target_id>[a-zA-Z0-9-]+)/relevancy_results$',
        FeatureRelevancyResultsView.as_view(),
        name='target-feature-relevancy_results'),
    url(r'targets/(?P<target_id>[a-zA-Z0-9-]+)/redundancy_results$',
        TargetRedundancyResults.as_view(),
        name='feature-redundancy_results'),
    url(r'targets/(?P<target_id>[a-zA-Z0-9-]+)/hics',
        FixedFeatureSetHicsView.as_view(),
        name='fixed-feature-set-hics'),

    # Distributions
    url(r'targets/(?P<target_id>[a-zA-Z0-9-]+)/distributions(?:/(?P<max_samples>[0-9]+))?$',
        ConditionalDistributionsView.as_view(), name='target-conditional-distributions'),

    # Calculations
    url(r'calculations$', CalculationListView.as_view(), name='calculation-list'),
]
