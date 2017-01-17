from django.conf.urls import url
from features.views import FeatureListView, FeatureSamplesView, DatasetListView, \
    FeatureHistogramView, FeatureSlicesView, TargetDetailView, DatasetViewUploadView


urlpatterns = [
    url(r'dataset/(?P<dataset_name>[a-zA-Z0-9_]+)$', FeatureListView.as_view(), name='feature-list'),
    url(r'datasets/(?P<dataset_name>[a-zA-Z0-9_]+)$/target$', TargetDetailView.as_view(), name='target-detail'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9_]+)/samples$', FeatureSamplesView.as_view(),
        name='feature-samples'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9_]+)/histogram$', FeatureHistogramView.as_view(),
        name='feature-histogram'),
    url(r'features/(?P<feature_id>[a-zA-Z0-9_]+)/slices$', FeatureSlicesView.as_view(),
        name='feature-slices'),
    url(r'datasets/upload/(?P<filename>[^/]+)$', DatasetViewUploadView.as_view(),
        name='dataset-upload'),
    url(r'datasets$', DatasetListView.as_view(),
        name='dataset-list')
]
