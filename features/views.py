from rest_framework.views import APIView
from features.models import Feature, Histogram
from features.serializers import FeatureSerializer, BinSerializer, SliceSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class FeatureListView(APIView):
    def get(self, *args, **kwargs):
        features = Feature.objects.all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class SelectTargetView(APIView):
    def post(self, _, feature_name):
        feature = get_object_or_404(Feature, name=feature_name)
        feature.select_as_target()
        serializer = FeatureSerializer(instance=feature)
        return Response(serializer.data)


class FeatureSamplesView(APIView):
    pass


class FeatureHistogramView(APIView):
    def get(self, _, feature_name):
        bins = get_object_or_404(Histogram, feature__name=feature_name).bin_set
        serializer = BinSerializer(instance=bins, many=True)
        return Response(serializer.data)


class FeatureSlicesView(APIView):
    def get(self, _, feature_name):
        slices = get_object_or_404(Feature, name=feature_name).slice_set
        serializer = SliceSerializer(instance=slices, many=True)
        return Response(serializer.data)
