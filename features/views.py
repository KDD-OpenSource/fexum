from rest_framework.views import APIView
from features.models import Feature, Bin, Sample, Dataset, Experiment, Result, Slice, Relevancy, Redundancy, Spectrogram
from features.serializers import FeatureSerializer, BinSerializer, ExperimentSerializer, \
    SampleSerializer, SliceSerializer, DatasetSerializer, RedundancySerializer, \
    ExperimentTargetSerializer, RelevancySerializer, FeatureSliceSerializer, \
    ConditionalDistributionRequestSerializer, ConditionalDistributionResultSerializer, DensitySerializer, \
    SpectrogramSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT
from features.tasks import calculate_hics, calculate_conditional_distributions, initialize_from_dataset,\
    calculate_densities
from rest_framework.parsers import MultiPartParser, FormParser
import logging
import zipfile
from features.exceptions import NoCSVInArchiveFoundError, NotZIPFileError
from django.core.files import File
from django.utils.datastructures import MultiValueDictKeyError
from celery import chain


logger = logging.getLogger(__name__)


class ExperimentListView(APIView):
    def get(self, request):
        experiments = Experiment.objects.filter(user=request.user).all()
        serializer = ExperimentSerializer(instance=experiments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ExperimentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)


class ExperimentDetailView(APIView):
    def get(self, request, experiment_id):
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
        serializer = ExperimentSerializer(instance=experiment)
        return Response(serializer.data)


class TargetDetailView(APIView):
    def put(self, request, experiment_id):
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
        serializer = ExperimentTargetSerializer(instance=experiment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        number_of_iterations = 10
        tasks = [calculate_hics.subtask(immutable=True,
                                        kwargs={'target_id': serializer.instance.target.id})] * number_of_iterations
        chain(tasks).apply_async()

        return Response(serializer.data)

    def delete(self, request, experiment_id):
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
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
            dataset = Dataset.objects.create(
                name=zip_csv_file.name,
                content=csv_file,
                uploaded_by=request.user)

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


class FeatureDensityView(APIView):
    def get(self, _, feature_id, target_id):
        get_object_or_404(Feature, id=feature_id)
        get_object_or_404(Feature, id=target_id)

        densities_task = calculate_densities.apply_async(args=[target_id, feature_id])
        densities = densities_task.get()
        serializer = DensitySerializer(instance=densities, many=True)
        return Response(serializer.data)


class FeatureHistogramView(APIView):
    def get(self, _, feature_id):
        feature = get_object_or_404(Feature, id=feature_id)
        bins = Bin.objects.filter(feature=feature).order_by('id').all()
        serializer = BinSerializer(instance=bins, many=True)
        return Response(serializer.data)


class FeatureSpectrogramView(APIView):
    def get(self, _, feature_id):
        feature = get_object_or_404(Feature, id=feature_id)
        spectrogram = get_object_or_404(Spectrogram, feature=feature)
        serializer = SpectrogramSerializer(instance=spectrogram)
        return Response(serializer.data)


class FeatureSlicesView(APIView):
    def get(self, _, target_id, feature_id):
        target = get_object_or_404(Feature, pk=target_id)
        feature = get_object_or_404(Feature, pk=feature_id)
        rar_result = Result.objects.get(target=target)
        slices = Slice.objects.filter(relevancy__rar_result=rar_result,
                                      relevancy__feature=feature)
        serializer = SliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class FeatureRelevancyResultsView(APIView):
    def get(self, _, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        # TODO: Filter for same result set
        rar_result = Result.objects.filter(target=target).last()
        relevancies = Relevancy.objects.filter(rar_result=rar_result)
        serializer = RelevancySerializer(instance=relevancies, many=True)
        return Response(serializer.data)


class TargetRedundancyResults(APIView):
    def get(self, _, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        rar_result = Result.objects.filter(target=target).last()
        redundancies = Redundancy.objects.filter(rar_result=rar_result)
        serializer = RedundancySerializer(instance=redundancies, many=True)
        return Response(serializer.data)


class FilteredSlicesView(APIView):
    def get(self, request, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        feature_ids = request.query_params.get('feature__in', '').split(',')
        rar_result = Result.objects.get(target=target)
        slices = Slice.objects.filter(relevancy__rar_result=rar_result,
                                      relevancy__feature_id__in=feature_ids)
        serializer = FeatureSliceSerializer(instance=slices, many=True)
        return Response(serializer.data)


class CondiditonalDistributionsView(APIView):
    def post(self, request, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        serializer = ConditionalDistributionRequestSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # Execute calculation on worker and get a synchronous result back to the client
        asnyc_result = calculate_conditional_distributions.apply_async(
            args=[target.id, [dict(data) for data in serializer.data]],
        )

        # Serialize and validate output
        results = asnyc_result.get()
        response_serializer = ConditionalDistributionResultSerializer(data=results, many=True)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.validated_data)

