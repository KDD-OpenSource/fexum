from rest_framework.views import APIView
from features.models import Feature, Bin, Target, Sample
from features.serializers import FeatureSerializer, BinSerializer, TargetSerializer, SampleSerializer, SliceSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_rar


class FeatureListView(APIView):
    def get(self, *args, **kwargs):
        features = Feature.objects.all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class FeatureSamplesView(APIView):
    def get(self, _, feature_name):
        samples = Sample.objects.filter(feature__name=feature_name).all()
        serializer = SampleSerializer(instance=samples, many=True)
        return Response(serializer.data)


class FeatureHistogramView(APIView):
    def get(self, _, feature_name):
        feature = get_object_or_404(Feature, name=feature_name)
        bins = Bin.objects.filter(feature=feature).order_by('id').all()
        serializer = BinSerializer(instance=bins, many=True)
        return Response(serializer.data)


class FeatureSlicesView(APIView):
    def get(self, _, feature_name):
        slices = get_object_or_404(Feature, name=feature_name).slice_set
        serializer = SliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class TargetDetailView(APIView):
    def put(self, request):
        target = Target.load()
        feature_name = request.data.get('feature', {}).get('name', None)
        feature = get_object_or_404(Feature, name=feature_name)
        target.feature = feature
        target.save()
        # TODO: Test

        calculate_rar.delay('')

        serializer = TargetSerializer(target)
        return Response(serializer.data)

    def get(self, _):
        target = Target.load()
        serializer = TargetSerializer(instance=target)
        return Response(serializer.data)

    def delete(self, _):
        Target.objects.all().delete()
        return Response(status=HTTP_204_NO_CONTENT)

