from rest_framework.views import APIView
from features.models import Feature, Bin, Target, Sample, Dataset
from features.serializers import FeatureSerializer, BinSerializer, TargetSerializer, \
    SampleSerializer, SliceSerializer, DatasetSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_rar
from rest_framework.parsers import FileUploadParser
from features.tasks import initialize_from_dataset, calculate_feature_statistics, build_histogram, \
    downsample_feature


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


class DatasetViewUploadView(APIView):
    parser_classes = (FileUploadParser,)

    def post(self, request, filename, *args, **kwargs):
        file_obj = request.FILES['file']
        dataset = Dataset.objects.create(name=filename, content=file_obj)

        # Start tasks for feature calculation
        # TODO: Make sure that initialize_from_dataset runs before everything else
        initialize_from_dataset.delay(dataset.id)

        serializer = DatasetSerializer(instance=dataset)

        return Response(serializer.data)


class DatasetListView(APIView):
    def get(self, _):
        datasets = Dataset.objects.all()
        serializer = DatasetSerializer(instance=datasets, many=True)
        return Response(serializer.data)
