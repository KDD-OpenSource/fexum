from __future__ import absolute_import, unicode_literals
from celery import shared_task
from sklearn.neighbors import KernelDensity
from features.models import Feature, Bin, Slice, Dataset, ResultCalculationMap, \
    Redundancy, Relevancy, Spectrogram, Calculation
from celery.task import chord
from celery.utils.log import get_task_logger
from multiprocessing import Manager
import SharedArray as sa
from pandas import DataFrame, read_csv
import numpy as np
from hics.incremental_correlation import IncrementalCorrelation
from hics.result_storage import AbstractResultStorage
from hics.scored_slices import ScoredSlices
from features.bindings import CalculationBinding, DatasetBinding
from time import time
from celery.schedules import crontab
from celery.decorators import periodic_task
from scipy.stats import zscore
from django.conf import settings
import os
from math import log
from ccwt import fft, frequency_band, render_png, EQUIPOTENTIAL
from django.db.models import Count, F
from features.serializers import FeatureSerializer

logger = get_task_logger(__name__)

# Locking of shared memory
_manager = Manager()
_dataframe_columns = _manager.dict()
_dataframe_lock = _manager.Lock()
_dataframe_last_access = _manager.dict()

# Fix bindings in celery context
DatasetBinding.register()
CalculationBinding.register()


# TODO: Write test
def _get_dataframe(dataset_id: str) -> DataFrame:
    """
    Get a dataset from the system's shared memory (/dev/shm). If it can't be found, it blocks all access to load it.

    IMPORTANT NOTE: Datasets get removed after 1 hour if they are not used. This means that if you use a really long running
    task, you have to update dataframe_last_access manually!

    :param dataset_id: The uuid of a dataset
    :return: Pandas Dataframe containing the whole dataset
    """

    _dataframe_lock.acquire()

    dataset_id = str(dataset_id)

    # Update last_access time with UNIX timestamp
    _dataframe_last_access[dataset_id] = time()

    # Either fetch RAM or load the dataset from disk
    try:
        shared_array = sa.attach('shm://{0}'.format(dataset_id))
        columns = _dataframe_columns[dataset_id]

        logger.info('Cache hit for dataset {0}'.format(dataset_id))
    except FileNotFoundError:
        logger.info('Cache miss for dataset {0}'.format(dataset_id))

        # Fetch dataset from disk and put it into RAM
        dataset = Dataset.objects.get(pk=dataset_id)
        filename = dataset.content.path
        dataframe = read_csv(filename)
        shared_array = sa.create('shm://{0}'.format(dataset_id), dataframe.shape)
        shared_array[:] = dataframe.values
        columns = dataframe.columns
        _dataframe_columns[dataset_id] = columns
        del dataframe

        logger.info('Cache save for dataset {0}'.format(dataset_id))

    dataframe = DataFrame(shared_array, columns=columns)

    _dataframe_lock.release()
    return dataframe


@shared_task
def calculate_feature_statistics(feature_id):
    feature = Feature.objects.get(pk=feature_id)

    dataframe = _get_dataframe(feature.dataset.id)
    feature_col = dataframe[feature.name]

    feature.min = np.amin(feature_col).item()
    feature.max = np.amax(feature_col).item()
    feature.mean = np.mean(feature_col).item()
    feature.variance = np.nanvar(feature_col).item()
    unique_values = np.unique(feature_col)
    integer_check = (np.mod(unique_values, 1) == 0).all()
    feature.is_categorical = integer_check and (unique_values.size < 10)
    if feature.is_categorical:
        feature.categories = list(unique_values)
    feature.save(update_fields=['min', 'max', 'variance', 'mean', 'is_categorical', 'categories'])

    del unique_values, feature


@shared_task
def calculate_densities(target_feature_id, feature_id):
    feature = Feature.objects.get(pk=feature_id)
    target_feature = Feature.objects.get(pk=target_feature_id)

    df = _get_dataframe(feature.dataset.id)
    target_col = df[target_feature.name]
    categories = target_feature.categories

    def calc_density(category):
        kde = KernelDensity(kernel='gaussian', bandwidth=0.75)
        X = df[target_col == category][feature.name]
        # Fitting requires expanding dimensions
        X = np.expand_dims(X, axis=1)
        kde.fit(X)
        # We'd like to sample 100 values
        X_plot = np.linspace(feature.min, feature.max, 100)
        # We need the last dimension again
        X_plot = np.expand_dims(X_plot, axis=1)
        log_dens = kde.score_samples(X_plot)
        return np.exp(log_dens).tolist()

    return [{'target_class': category, 'density_values': calc_density(category)} for category in categories]


@shared_task
def build_spectrogram(feature_id, width=256, height=128, frequency_base=1.0):
    """
    Builds a spectrogram using @Lichtso's ccwt library

    :param feature_id: The feature uuid to be analyzed.
    :param width: Width of the exported image (should be smaller than the number of samples)
    :param height: Height of the exported image
    :param frequency_base: Base for exponential frequency scales or 1.0 for linear scale
    """
    feature = Feature.objects.get(pk=feature_id)
    df = _get_dataframe(feature.dataset.id)

    feature_column = zscore(df[feature.name].values)
    fourier_transformed_signal = fft(feature_column)

    minimum_frequency = 0.001 * len(feature_column)
    maximum_frequency = 0.5 * len(feature_column)
    if frequency_base == 1.0:
        # Linear
        frequency_band_result = frequency_band(height, maximum_frequency - minimum_frequency, minimum_frequency)
    else:
        minimum_octave = log(minimum_frequency) / log(frequency_base)
        maximum_octave = log(maximum_frequency) / log(frequency_base)
        # Exponential
        frequency_band_result = frequency_band(height, maximum_octave - minimum_octave, minimum_octave, frequency_base)

    # Write into the spectrogram path
    filename = '{0}/spectrograms/{1}.png'.format(settings.MEDIA_ROOT, feature_id)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as output_file:
        render_png(output_file, EQUIPOTENTIAL, 0.0, fourier_transformed_signal, frequency_band_result, width)

    Spectrogram.objects.create(
        feature=feature,
        width=width,
        height=height,
        image=filename
    )


@shared_task
def build_histogram(feature_id, bins=50):
    feature = Feature.objects.get(pk=feature_id)

    if feature.is_categorical:
        bins = len(feature.categories)

    # Only read column with that name
    dataframe = _get_dataframe(feature.dataset.id)

    bin_set = []
    bins, bin_edges = np.histogram(dataframe[feature.name], bins=bins)
    for bin_index, bin_value in enumerate(bins):
        from_value = bin_edges[bin_index]
        to_value = bin_edges[bin_index + 1]
        bin = Bin(
            feature=feature,
            from_value=from_value,
            to_value=to_value,
            count=bin_value
        )
        bin_set.append(bin)
    Bin.objects.bulk_create(bin_set)

    del bins, bin_edges, bin_set


@shared_task
def get_samples(feature_id, max_samples=None):
    if not max_samples:
        max_samples = 10000
    feature = Feature.objects.get(pk=feature_id)
    df = _get_dataframe(feature.dataset.id)
    samples = df.loc[:, feature.name][::np.int(np.ceil(len(df) / max_samples))]
    return {str(feature_id): list(samples)}


@shared_task
def calculate_hics(calculation_id, feature_ids=[], bivariate=True, calculate_supersets=False, calculate_redundancies=False):
    class DjangoHICSResultStorage(AbstractResultStorage):
        def __init__(self, result_calculation_map, features):
            self.features = features
            self.feature_ids = [feature.id for feature in self.features]
            self.target = result_calculation_map.target
            self.result_calculation_map = result_calculation_map

        def get_relevancies(self):
            relevancies = Relevancy.objects.filter(result_calculation_map=self.result_calculation_map).all()
            feature_set_list = []
            relevancy_list = []
            iteration_list = []

            for relevancy in relevancies:
                feature_set_list += [tuple([feature.name for feature in relevancy.features.all()])]
                relevancy_list += [relevancy.relevancy]
                iteration_list += [relevancy.iteration]

            dataframe = DataFrame({'relevancy': relevancy_list, 'iteration': iteration_list},
                                  index=feature_set_list)

            return dataframe

        def update_relevancies(self, new_relevancies: DataFrame):
            for feature_set, data in new_relevancies.iterrows():
                features = Feature.objects.filter(name__in=list(feature_set), id__in=self.feature_ids).all()

                relevancy_query = Relevancy.objects.filter(result_calculation_map=self.result_calculation_map)
                relevancy_query = relevancy_query.annotate(feature_count=Count('features')).filter(feature_count=len(features))
                for feature in features:
                    relevancy_query = relevancy_query.filter(features=feature)

                if relevancy_query.count() == 0:
                    relevancy_object = Relevancy.objects.create(result_calculation_map=self.result_calculation_map, relevancy=data['relevancy'], iteration=data['iteration'])
                    relevancy_object.features.set(list(features))
                elif relevancy_query.count() == 1:
                    relevancy_object = relevancy_query.first()
                    relevancy_object.relevancy = data['relevancy']
                    relevancy_object.iteration = data['iteration']
                else:
                    raise AssertionError('Should not reach this condition')

                relevancy_object.save()

        def get_redundancies(self):
            feature_names = [feature.name for feature in self.features]
            redundancies_dataframe = DataFrame(data=0, columns=feature_names, index=feature_names)
            weights_dataframe = DataFrame(data=0, columns=feature_names, index=feature_names)

            redundancies = Redundancy.objects.filter(first_feature__in=self.features,
                                                     second_feature__in=self.features,
                                                     result_calculation_map=self.result_calculation_map).all()

            for redundancy in redundancies:
                first_feature_name = redundancy.first_feature.name
                second_feature_name = redundancy.second_feature.name
                redundancies_dataframe.loc[first_feature_name, second_feature_name] = redundancy.redundancy
                redundancies_dataframe.loc[second_feature_name, first_feature_name] = redundancy.redundancy
                weights_dataframe.loc[first_feature_name, second_feature_name] = redundancy.weight
                weights_dataframe.loc[second_feature_name, first_feature_name] = redundancy.weight

            if np.isinf(redundancies_dataframe).any().any():
                raise AssertionError('redundancy must not be inf (get)')

            return redundancies_dataframe, weights_dataframe

        def update_redundancies(self, new_redundancies: DataFrame, new_weights: DataFrame):
            if np.isinf(new_redundancies).any().any():
                raise AssertionError('redundancy must not be inf (update)')

            for first_feature in self.features:
                for second_feature in self.features:
                    if first_feature.id < second_feature.id:
                        Redundancy.objects.update_or_create(
                            result_calculation_map=self.result_calculation_map,
                            first_feature=first_feature,
                            second_feature=second_feature,
                            defaults={'redundancy': new_redundancies.loc[first_feature.name, second_feature.name], 'weight': new_weights.loc[first_feature.name, second_feature.name]})

        def get_slices(self):
            slices = Slice.objects.filter(features__in=self.features,
                                          result_calculation_map=self.result_calculation_map)
            return {
                tuple([feature.name for feature in slice.features.all()]): ScoredSlices.from_dict(slice.object_definition)
                for slice in slices}

        def update_slices(self, new_slices: dict()):
            name_mapping = lambda name: str(Feature.objects.get(name=name, dataset=self.target.dataset).id)
            for feature_set, slices in new_slices.items():
                features = Feature.objects.filter(name__in=feature_set, dataset=self.target.dataset).all()

                slice_query = Slice.objects.filter(result_calculation_map=self.result_calculation_map)
                slice_query = slice_query.annotate(feature_count=Count('features')).filter(feature_count=len(features))
                for feature in features:
                    slice_query = slice_query.filter(features=feature)

                if slice_query.count() == 0:
                    slice_object = Slice.objects.create(result_calculation_map=self.result_calculation_map)
                    slice_object.features.set(list(features))
                elif slice_query.count() == 1:
                    slice_object = slice_query.first()
                else:
                    raise AssertionError('Should not reach this condition')

                slice_object.object_definition = slices.to_dict()
                slice_object.output_definition = slices.to_output(name_mapping)
                slice_object.save()

    assert not bivariate or (len(feature_ids) == 0)  # If bivarite true, then features_ids has to be empty
    assert not bivariate or not calculate_supersets  # bivariate => not calculate_superset
    assert not calculate_supersets or (len(feature_ids) > 0)  # superset => len > 0

    calculation = Calculation.objects.get(id=calculation_id)
    result_calculation_map = calculation.result_calculation_map
    target = result_calculation_map.target
    dataframe = _get_dataframe(target.dataset.id)
    features = Feature.objects.filter(dataset=target.dataset).exclude(id=target.id).all()
    categorical_features = Feature.objects.filter(dataset=target.dataset, is_categorical=True).all()
    categorical_feature_names = [feature.name for feature in categorical_features if feature.is_categorical]

    result_storage = DjangoHICSResultStorage(result_calculation_map=result_calculation_map, features=features)
    correlation = IncrementalCorrelation(data=dataframe, target=target.name, result_storage=result_storage,
                                         iterations=10, alpha=0.1, categorical_features=categorical_feature_names)

    # Calculate relevancies
    if bivariate:
        correlation.update_bivariate_relevancies(runs=5)
    elif not bivariate and len(feature_ids) == 0:
        correlation.update_multivariate_relevancies(k=5, runs=50)
    elif not bivariate and len(feature_ids) > 0:
        feature_names = [feature.name for feature in Feature.objects.filter(id__in=feature_ids).all()]
        if calculate_supersets:
            correlation.update_multivariate_relevancies(feature_names, k=5, runs=10)
        else:
            correlation.update_multivariate_relevancies(feature_names, k=len(feature_names), runs=5)
    else:
        raise AssertionError('Should not reach this condition')

    # Calculate redundancies
    if bivariate and calculate_redundancies:
        correlation.update_redundancies(k=5, runs=20)

    calculation.current_iteration += 1
    calculation.save()
    # Calculation.objects.filter(id=calculation.id).update(current_iteration=F('current_iteration')+1)


@shared_task
def initialize_from_dataset(dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    dataset.status = Dataset.PROCESSING  # TODO: Test
    dataset.save(update_fields=['status'])

    dataframe = _get_dataframe(dataset_id)

    # Only read first row for header
    headers = list(dataframe.columns.values)
    feature_ids = [Feature.objects.create(name=header, dataset=dataset).id for header in headers]

    # Chaining with Celery would be more beautiful...
    calculate_feature_statistics_subtasks = [
        calculate_feature_statistics.subtask(immutable=True, kwargs={'feature_id': feature_id}) for feature_id in
        feature_ids]
    build_spectrogram_subtasks = [build_spectrogram.subtask(immutable=True, kwargs={'feature_id': feature_id}) for
                                  feature_id in feature_ids]
    build_histogram_subtasks = [build_histogram.subtask(immutable=True, kwargs={'feature_id': feature_id}) for
                                feature_id in feature_ids]

    subtasks = calculate_feature_statistics_subtasks + build_spectrogram_subtasks + build_histogram_subtasks

    chord(subtasks)(initialize_from_dataset_processing_callback.subtask(kwargs={'dataset_id': dataset_id}))


@shared_task
def initialize_from_dataset_processing_callback(*args, **kwargs):
    dataset_id = kwargs['dataset_id']
    dataset = Dataset.objects.get(id=dataset_id)
    dataset.status = Dataset.DONE
    dataset.save(update_fields=['status'])


@shared_task
def calculate_conditional_distributions(target_id, feature_constraints, max_samples=None) -> dict:
    target = Feature.objects.get(pk=target_id)

    logger.info(
        'Started for target {0} and features ranges/categories {1}'.format(target_id, feature_constraints))

    df = _get_dataframe(dataset_id=target.dataset.id)

    # Convert feature ids to feature name for using it in dataframe and store feature ids in dict
    feature_ids = {target.name: str(target_id)}
    for feature_constraint in feature_constraints:
        feature_name = Feature.objects.get(dataset_id=target.dataset.id,
                                           id=feature_constraint['feature']).name
        feature_ids[feature_name] = str(feature_constraint['feature'])
        feature_constraint['feature'] = feature_name

    logger.info('Changed feature range to {0}'.format(feature_constraints))

    # Make filtering based on category or range
    filter_list = np.array([True] * len(df))
    for ftr in feature_constraints:
        if 'range' in ftr:
            filter_list = np.logical_and(df[ftr['feature']] >= ftr['range']['from_value'], filter_list)
            filter_list = np.logical_and(df[ftr['feature']] <= ftr['range']['to_value'], filter_list)

        elif 'categories' in ftr:
            filter_list = np.logical_and(df[ftr['feature']].isin(ftr['categories']), filter_list)

    # Calculate conditional probabilites based on filtering
    sliced_df = df.loc[filter_list, :]
    values, counts = np.unique(sliced_df.loc[:, target.name], return_counts=True)
    probabilities = counts / filter_list.sum()

    # Convert to result dict
    result = {
        'distribution':
            [{'value': float(probs[0]), 'probability': probs[1]} for probs in zip(values, probabilities)],
    }

    # Subsample dataframe
    if max_samples:
        feature_names = [str(ftr['feature']) for ftr in feature_constraints] + [target.name]
        samples = DataFrame(sliced_df.loc[:, feature_names][::max(np.int(np.ceil(len(sliced_df) / max_samples)), 1)])
        result['samples'] = {feature_ids[column]: list(samples.loc[:, column]) for column in samples.columns}

    logger.info('Result: {0}'.format(result))

    """
    e.g.
    {
        'distribution': [{'value': 0.0, 'probability': 1.0}],
        'samples': {
            id('Col1'): [0.0, 0.0],
            id('Col2'): [-0.046074360000000002, -0.047435999999999999],
            id('Col3'): [0.0, 0.0]
        }
    }
    """
    return result


@periodic_task(run_every=(crontab(minute=15)), ignore_result=True)
def remove_unused_dataframes(max_delta=3600):
    """
    Delete all in-memory information of a dataset if it wasn't accessed in the last max_delta seconds

    :param max_delta: Maximum delta in seconds
    """
    _dataframe_lock.acquire()

    min_time = time() - max_delta
    for dataset_id, timestamp in _dataframe_last_access.items():
        if timestamp < min_time:
            del _dataframe_last_access[dataset_id]
            del _dataframe_columns[dataset_id]
            sa.delete(dataset_id)

    _dataframe_lock.release()
