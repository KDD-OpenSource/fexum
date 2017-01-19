from django.conf.urls import url
from features.views import FeatureListView, FeatureSamplesView, DatasetListView, \
    FeatureHistogramView, FeatureSlicesView, TargetDetailView, DatasetViewUploadView, \
    SessionListView, FeatureRarResultsView, SessionDetailView


urlpatterns = [
    # Sessions
    url(r'sessions$', SessionListView.as_view(), name='session-list'),
    url(r'sessions/(?P<session_id>[a-zA-Z0-9-]+)$', SessionDetailView.as_view(),
        name='session-detail'),
    url(r'sessions/(?P<session_id>[a-zA-Z0-9-]+)/target$', TargetDetailView.as_view(),
        name='session-targets-detail'),

    # Datasets
    url(r'datasets$', DatasetListView.as_view(), name='dataset-list'),
    url(r'datasets/upload$', DatasetViewUploadView.as_view(), name='dataset-upload'),
    url(r'datasets/(?P<dataset_id>[a-zA-Z0-9-]+)/features$', FeatureListView.as_view(),
        name='dataset-features-list'),

    # Features
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/samples$', FeatureSamplesView.as_view(),
        name='feature-samples'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9-]+)/histogram$', FeatureHistogramView.as_view(),
        name='feature-histogram'),

    # Results
    url(r'sessions/(?P<session_id>[a-zA-Z0-9-]+)/features/(?P<feature_id>[a-zA-Z0-9-]+)/slices$',
        FeatureSlicesView.as_view(),
        name='session-feature-slices'),
    url(r'sessions/(?P<session_id>[a-zA-Z0-9-]+)/rar_results$',
        FeatureRarResultsView.as_view(),
        name='session-feature-rar_results'),
]
