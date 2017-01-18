from rest_framework.views import APIView
from features.models import Feature, Bin, Sample, Dataset, Session, RarResult, Slice
from features.serializers import FeatureSerializer, BinSerializer, SessionSerializer, \
    SampleSerializer, SliceSerializer, DatasetSerializer, RarResultSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_rar
from rest_framework.parsers import FileUploadParser
from features.tasks import initialize_from_dataset, calculate_feature_statistics, build_histogram, \
    downsample_feature
from django.contrib.auth import get_user_model


# Helper if we only want one user, TODO: replace with request.user
def get_user():
    try:
        user = get_user_model().objects.get()
    except get_user_model().DoesNotExist:
        user = get_user_model().objects.create()

    return user


class SessionListView(APIView):
    def get(self, _):
        user = get_user()
        sessions = Session.objects.filter(user=user).all()
        serializer = SessionSerializer(instance=sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = get_user()
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data)


class SessionDetailView(APIView):
    def get(self, _):
        user = get_user()
        session = get_object_or_404(Session, user=user)
        serializer = SessionSerializer(instance=session)
        return Response(serializer.data)


class TargetDetailView(APIView):
    def put(self, request, session_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        target_id = request.data.get('target', None)
        target = get_object_or_404(Feature, pk=target_id)
        session.save(target=target)
        # TODO: Test

        calculate_rar.delay(dataset_id=session.dataset.id)

        return Response(status=HTTP_204_NO_CONTENT)

    def delete(self, _, session_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        session.target = None
        session.save()
        return Response(status=HTTP_204_NO_CONTENT)


class DatasetListView(APIView):
    def get(self, _):
        datasets = Dataset.objects.all()
        serializer = DatasetSerializer(instance=datasets, many=True)
        return Response(serializer.data)


class DatasetViewUploadView(APIView):
    parser_classes = (FileUploadParser,)

    def post(self, request, filename, *args, **kwargs):
        file_obj = request.FILES['file']
        dataset = Dataset.objects.create(name=filename, content=file_obj)

        # Start tasks for feature calculation
        # TODO: Make sure that initialize_from_dataset runs before everything else
        initialize_from_dataset.delay(dataset_id=dataset.id)

        serializer = DatasetSerializer(instance=dataset)

        return Response(serializer.data)


class FeatureListView(APIView):
    def get(self, _, dataset_id):
        dataset = get_object_or_404(Dataset, pk=dataset_id)
        features = Feature.objects.filter(dataset=dataset).all()
        serializer = FeatureSerializer(instance=features, many=True)
        return Response(serializer.data)


class FeatureSamplesView(APIView):
    def get(self, _, feature_id):
        samples = Sample.objects.filter(feature_id=feature_id).all()
        serializer = SampleSerializer(instance=samples, many=True)
        return Response(serializer.data)


class FeatureHistogramView(APIView):
    def get(self, _, feature_id):
        feature = get_object_or_404(Feature, id=feature_id)
        bins = Bin.objects.filter(feature=feature).order_by('id').all()
        serializer = BinSerializer(instance=bins, many=True)
        return Response(serializer.data)


class FeatureSlicesView(APIView):
    def get(self, _, session_id, feature_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        feature = get_object_or_404(Feature, pk=feature_id)
        slices = Slice.objects.filter(rar_result__target=session.target,
                                      rar_result__feature=feature)
        serializer = SliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class FeatureRarResultsView(APIView):
    def get(self, _, session_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        rar_results = RarResult.objects.filter(feature__dataset=session.dataset)
        serializer = RarResultSerializer(instance=rar_results, many=True)
        return Response(serializer.data)
