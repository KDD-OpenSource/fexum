from rest_framework.views import APIView
from features.models import Feature, Bin, Sample, Dataset, Experiment, RelevancyResult, \
    RedundancyResult, Slice
from features.serializers import FeatureSerializer, BinSerializer, ExperimentSerializer, \
    SampleSerializer, SliceSerializer, DatasetSerializer, RedundancyResultSerializer, \
    ExperimentTargetSerializer, RelevancyResultSerializer, FeatureSliceSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_rar, calculate_conditional_distributions
from rest_framework.parsers import MultiPartParser, FormParser
from features.tasks import initialize_from_dataset
from django.contrib.auth import get_user_model
import logging
import zipfile
from features.exceptions import NoCSVInArchiveFoundError, NotZIPFileError
from django.core.files import File
from django.utils.datastructures import MultiValueDictKeyError


logger = logging.getLogger(__name__)


# Helper to mock an authenticated user TODO: replace with request.user
def get_user():
    user = get_user_model().objects.first() 
    if user is None:
        user = get_user_model().objects.create()
    return user


class ExperimentListView(APIView):
    def get(self, _):
        user = get_user()
        experiments = Experiment.objects.filter(user=user).all()
        serializer = ExperimentSerializer(instance=experiments, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = get_user()
        serializer = ExperimentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data)


class ExperimentDetailView(APIView):
    def get(self, _, experiment_id):
        user = get_user()
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=user)
        serializer = ExperimentSerializer(instance=experiment)
        return Response(serializer.data)


class TargetDetailView(APIView):
    def put(self, request, experiment_id):
        user = get_user()
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=user)
        serializer = ExperimentTargetSerializer(instance=experiment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        calculate_rar.delay(target_id=serializer.instance.target.id)

        return Response(serializer.data)

    def delete(self, _, experiment_id):
        user = get_user()
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=user)
        experiment.target = None
        experiment.save()
        return Response(status=HTTP_204_NO_CONTENT)


class DatasetListView(APIView):
    def get(self, _):
        datasets = Dataset.objects.all()
        serializer = DatasetSerializer(instance=datasets, many=True)
        return Response(serializer.data)


class DatasetViewUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser,)

    def put(self, request):
        try:
            zip_file = request.FILES['file']
            archive = zipfile.ZipFile(zip_file)
        except (MultiValueDictKeyError, zipfile.BadZipfile):
            raise NotZIPFileError

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
    def get(self, _, target_id, feature_id):
        target = get_object_or_404(Feature, pk=target_id)
        feature = get_object_or_404(Feature, pk=feature_id)
        slices = Slice.objects.filter(relevancy_result__target=target,
                                      relevancy_result__feature=feature)
        serializer = SliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class FeatureRelevancyResultsView(APIView):
    def get(self, _, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        relevancy_results = RelevancyResult.objects.filter(target=target)
        serializer = RelevancyResultSerializer(instance=relevancy_results, many=True)
        return Response(serializer.data)


class DatasetRedundancyResults(APIView):
    def get(self, _, dataset_id):
        dataset = get_object_or_404(Dataset, pk=dataset_id)
        redundancy_results = RedundancyResult.objects.filter(first_feature__dataset=dataset,
                                                             second_feature__dataset=dataset)
        serializer = RedundancyResultSerializer(instance=redundancy_results, many=True)
        return Response(serializer.data)


class FilteredSlicesView(APIView):
    def get(self, request, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        feature_ids = request.query_params.get('feature__in', '').split(',')
        slices = Slice.objects.filter(relevancy_result__target=target,
                                      relevancy_result__feature_id__in=feature_ids)
        serializer = FeatureSliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class CondiditonalDistributionsView(APIView):
    def post(self, request, target_id):
        # Execute calculation on worker an get a synchronous result back to the client
        asnyc_result = calculate_conditional_distributions.apply_async(target_id=target_id, feature_ranges=request.data)
        data = asnyc_result.get()
        return Response(data)
