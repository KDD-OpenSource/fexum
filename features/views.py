from rest_framework.views import APIView
from features.models import Feature, Bin, Sample, Dataset, Session, RarResult, Slice
from features.serializers import FeatureSerializer, BinSerializer, SessionSerializer, \
    SampleSerializer, SliceSerializer, DatasetSerializer, RarResultSerializer, \
    SessionTargetSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_rar
from rest_framework.parsers import MultiPartParser, FormParser
from features.tasks import initialize_from_dataset
from django.contrib.auth import get_user_model
import logging
import zipfile
from features.exceptions import NoCSVInArchiveFoundError
from django.core.files import File


logger = logging.getLogger(__name__)


# Helper to mock an authenticated user TODO: replace with request.user
def get_user():
    user = get_user_model().objects.first() 
    if user is None:
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
    def get(self, _, session_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        serializer = SessionSerializer(instance=session)
        return Response(serializer.data)


class TargetDetailView(APIView):
    def put(self, request, session_id):
        user = get_user()
        session = get_object_or_404(Session, pk=session_id, user=user)
        serializer = SessionTargetSerializer(instance=session, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        calculate_rar.delay(target_id=serializer.instance.target.id)

        return Response(serializer.data)

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
    parser_classes = (MultiPartParser, FormParser,)

    def put(self, request):
        zip_file = request.FILES['file']
        archive = zipfile.ZipFile(zip_file)
        try:
            csv_name = [item for item in archive.namelist() if item.endswith('csv')][0]
        except IndexError:
            raise NoCSVInArchiveFoundError

        with archive.open(csv_name) as zip_csv_file:
            # Convert zipfile handle to Django file handle
            csv_file = File(zip_csv_file)
            dataset = Dataset.objects.create(name=zip_csv_file.name, content=csv_file)

        # Start tasks for feature calculation
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
        rar_results = RarResult.objects.filter(feature__dataset=session.dataset,
                                               target=session.target)
        serializer = RarResultSerializer(instance=rar_results, many=True)
        return Response(serializer.data)
