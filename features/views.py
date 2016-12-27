from rest_framework.views import APIView
from features.models import Feature, Histogram, Target
from features.serializers import FeatureSerializer, BinSerializer, TargetSerializer, SliceSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT


class FeatureListView(APIView):
    def get(self, *args, **kwargs):
        features = Feature.objects.all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class SelectTargetView(APIView):
    def post(self, _, feature_name):
        feature = get_object_or_404(Feature, name=feature_name)
        target = Target.objects.create(feature=feature)
        serializer = TargetSerializer(instance=target)
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


class TargetDetailView(APIView):
    def get(self, _):
        target = get_object_or_404(Target)
        serializer = TargetSerializer(instance=target)
        return Response(serializer.data)

    def delete(self, _):
        target = get_object_or_404(Target)
        target.delete()
        return Response(status=HTTP_204_NO_CONTENT)

