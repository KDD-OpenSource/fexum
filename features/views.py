from rest_framework.views import APIView
from features.models import Feature
from features.serializers import FeatureSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class FeatureListView(APIView):
    def get(self, *args, **kwargs):
        features = Feature.objects.all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class SelectTargetView(APIView):
    def post(self, _, feature_name, *args, **kwargs):
        feature = get_object_or_404(Feature, name=feature_name)
        feature.select_as_target()
        feature.save()
        serializer = FeatureSerializer(instance=feature)
        return Response(serializer.data)


class FeatureSamplesView(APIView):
    pass


class FeatureHistogramView(APIView):
    pass


class FeatureSlicesView(APIView):
    pass
