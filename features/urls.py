from django.conf.urls import url
from features.views import FeatureListView, FeatureSamplesView, \
    FeatureHistogramView, FeatureSlicesView, TargetDetailView


urlpatterns = [
    url(r'features$', FeatureListView.as_view(), name='feature-list'),
    url(r'features/target$', TargetDetailView.as_view(), name='target-detail'),
    url(r'features/(?P<feature_name>[a-zA-Z0-9_]+)/samples$', FeatureSamplesView.as_view(),
        name='feature-samples'),
    url(r'features/(?P<feature_name>[a-zA-Z0-9_]+)/histogram$', FeatureHistogramView.as_view(),
        name='feature-histogram'),
    url(r'features/(?P<feature_name>[a-zA-Z0-9_]+)/slices$', FeatureSlicesView.as_view(),
        name='feature-slices')
]
