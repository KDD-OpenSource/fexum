from rest_framework.views import APIView
from features.models import Feature, Bin, Sample, Dataset, Experiment, Slice, Relevancy, Redundancy, Spectrogram, \
    ResultCalculationMap
from features.serializers import FeatureSerializer, BinSerializer, ExperimentSerializer, \
    SampleSerializer, DatasetSerializer, RedundancySerializer, \
    ExperimentTargetSerializer, RelevancySerializer, FeatureSliceSerializer, \
    ConditionalDistributionRequestSerializer, ConditionalDistributionResultSerializer, DensitySerializer, \
    SpectrogramSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from features.tasks import calculate_hics, calculate_conditional_distributions, initialize_from_dataset,\
    calculate_densities
from rest_framework.parsers import MultiPartParser, FormParser
import logging
import zipfile
from features.exceptions import NoCSVInArchiveFoundError, NotZIPFileError
from django.core.files import File
from django.utils.datastructures import MultiValueDictKeyError
from celery import chain
from django.db.models import Count
from features.models import Calculation

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
        number_of_iterations = 10

        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
        serializer = ExperimentTargetSerializer(instance=experiment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        target = Feature.objects.get(id=serializer.instance.target.id)
        result_calculation_map, __ = ResultCalculationMap.objects.get_or_create(target=target)
        calculation = Calculation.objects.create(type=Calculation.DEFAULT_HICS,
                                             result_calculation_map=result_calculation_map,
                                             max_iteration=number_of_iterations,
                                             current_iteration=0)

        tasks = [calculate_hics.subtask(immutable=True,
                                        kwargs={'calculation': calculation, 'calculate_redundancies': True})] * number_of_iterations
        chain(tasks).apply_async()

        return Response(serializer.data)

    def delete(self, request, experiment_id):
        experiment = get_object_or_404(Experiment, pk=experiment_id, user=request.user)
        experiment.target = None
        experiment.save()
        return Response(status=HTTP_204_NO_CONTENT)


class FixedFeatureSetHicsView(APIView):
    def post(self, request, target_id):
        target = get_object_or_404(Feature, id=target_id)
        result_calculation_map = ResultCalculationMap.objects.get(target=target)
        feature_ids = request.data.get('features') or []
        features_queryset = Feature.objects.filter(id__in=feature_ids, dataset=target.dataset)

        # Make sure that we filtered for all feature ids
        if features_queryset.count() != len(feature_ids) and len(feature_ids) > 0:
            return Response(status=HTTP_404_NOT_FOUND, data={'detail': 'Not found.'})

        features = features_queryset.all()

        calculation = Calculation.objects.create(type=Calculation.FIXED_FEATURE_SET_HICS,
                                             result_calculation_map=result_calculation_map,
                                             max_iteration=1,
                                             current_iteration=0)
        calculate_hics.apply_async(kwargs={
            'calculation': calculation,
            'feature_ids': [feature.id for feature in features],
            'bivariate': False,
            'calculate_supersets': False,
            'calculate_redundancies': False})

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
    def post(self, request, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        feature_ids = request.data.get('features') or []
        features_queryset = Feature.objects.filter(id__in=feature_ids, dataset=target.dataset)

        # Make sure that we filtered for all feature ids
        if features_queryset.count() != len(feature_ids) and len(feature_ids) > 0:
            return Response(status=HTTP_404_NOT_FOUND, data={'detail' : 'Not found.'})

        result = ResultCalculationMap.objects.filter(target=target).last()
        slices_queryset = Slice.objects.filter(result_calculation_map=result).annotate(feature_count=Count('features')).filter(feature_count=len(feature_ids))
        for feature in features_queryset.all():
            slices_queryset = slices_queryset.filter(features=feature)

        if slices_queryset.count() == 1:
            output_definition = slices_queryset.last().output_definition
        else:
            return Response([])
        return Response(output_definition)


class FeatureRelevancyResultsView(APIView):
    def get(self, _, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        # TODO: Filter for same result set
        result = ResultCalculationMap.objects.filter(target=target).last()
        relevancies = Relevancy.objects.annotate(feature_count=Count('features')).filter(result_calculation_map=result, feature_count=1)    # annotate to return only bivariate correlation 
        serializer = RelevancySerializer(instance=relevancies, many=True)
        return Response(serializer.data)


class TargetRedundancyResults(APIView):
    def get(self, _, target_id):
        target = get_object_or_404(Feature, pk=target_id)
        result = ResultCalculationMap.objects.filter(target=target).last()
        redundancies = Redundancy.objects.filter(result_calculation_map=result)
        serializer = RedundancySerializer(instance=redundancies, many=True)
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

