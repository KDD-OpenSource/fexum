from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample, Dataset, Result, \
    Redundancy, Relevancy, Spectrogram
from celery.task import chord
from celery.utils.log import get_task_logger
from multiprocessing import Manager
import SharedArray as sa
from hics.incremental_correlation import IncrementalCorrelation
from hics.result_storage import AbstractResultStorage
from hics.scored_slices import ScoredSlices
from features.bindings import ResultBinding, DatasetBinding
from time import time
from celery.schedules import crontab
from celery.decorators import periodic_task
import ccwt
from scipy.stats import zscore
from django.conf import settings
import os
from math import log


logger = get_task_logger(__name__)

# Locking of shared memory
manager = Manager()
dataframe_columns = manager.dict()
dataframe_lock = manager.Lock()
dataframe_last_access = manager.dict()

# Fix bindings in celery context
DatasetBinding.register()
ResultBinding.register()


# TODO: Write test
def _get_dataframe(dataset_id: str) -> pd.DataFrame:
    """
    Get a dataset from the system's shared memory (/dev/shm). If it can't be found, it blocks all access to load it.
    
    IMPORTANT NOTE: Datasets get removed after 1 hour if they are not used. This means that if you use a really long running 
    task, you have to update dataframe_last_access manually!
    
    :param dataset_id: The uuid of a dataset
    :return: Pandas Dataframe containing the whole dataset
    """

    dataframe_lock.acquire()

    dataset_id = str(dataset_id)

    # Update last_access time with UNIX timestamp
    dataframe_last_access[dataset_id] = time()

    # Either fetch RAM or load the dataset from disk
    try:
        shared_array = sa.attach('shm://{0}'.format(dataset_id))
        columns = dataframe_columns[dataset_id]

        logger.info('Cache hit for dataset {0}'.format(dataset_id))
    except FileNotFoundError:
        logger.info('Cache miss for dataset {0}'.format(dataset_id))

        # Fetch dataset from disk and put it into RAM
        dataset = Dataset.objects.get(pk=dataset_id)
        filename = dataset.content.path
        dataframe = pd.read_csv(filename)
        shared_array = sa.create('shm://{0}'.format(dataset_id), dataframe.shape)
        shared_array[:] = dataframe.values
        columns = dataframe.columns
        dataframe_columns[dataset_id] = columns
        del dataframe

        logger.info('Cache save for dataset {0}'.format(dataset_id))

    dataframe = pd.DataFrame(shared_array, columns=columns)

    dataframe_lock.release()
    return dataframe


class DjangoHICSResultStorage(AbstractResultStorage):
    def __init__(self, result, features):
        self.features = features
        self.target = result.target
        self.result = result

    def get_relevancies(self):
        relevancies = Relevancy.objects.filter(result=self.result).all()
        feature_set_list = []
        relevancy_list = []
        iteration_list = []

        for relevancy in relevancies:
            feature_set_list += [tuple([feature.name for feature in relevancy.features.all()])]
            relevancy_list += [relevancy.relevancy]
            iteration_list += [relevancy.iteration]

        dataframe = pd.DataFrame({'relevancy': relevancy_list, 'iteration': iteration_list},
                                 index=feature_set_list)

        return dataframe

    def update_relevancies(self, new_relevancies: pd.DataFrame):
        for feature_set, data in new_relevancies.iterrows():
            features = Feature.objects.filter(name__in=list(feature_set), id__in=self.features)
            Relevancy.objects.update_or_create(
                result=self.result,
                features=features,
                defaults={'iteration': data.iteration, 'relevancy': data.relevancy}
            )

    def get_redundancies(self):
        feature_names = [feature.name for feature in self.features]
        redundancies_dataframe = pd.DataFrame(data=0, columns=feature_names, index=feature_names)
        weights_dataframe = pd.DataFrame(data=0, columns=feature_names, index=feature_names)

        redundancies = Redundancy.objects.filter(first_feature__in=self.features,
                                                 second_feature__in=self.features,
                                                 result=self.result).all()
        for redundancy in redundancies:
            first_feature_name = redundancy.first_feature.name
            second_feature_name = redundancy.second_feature.name
            redundancies_dataframe[first_feature_name, second_feature_name] = redundancy.redundancy
            redundancies_dataframe[second_feature_name, first_feature_name] = redundancy.redundancy
            weights_dataframe[first_feature_name, second_feature_name] = redundancy.weight
            weights_dataframe[second_feature_name, first_feature_name] = redundancy.weight

        return redundancies_dataframe, weights_dataframe

    def update_redundancies(self, new_redundancies: pd.DataFrame, new_weights: pd.DataFrame):
        for first_feature in self.features:
            for second_feature in self.features:
                Redundancy.objects.update_or_create(
                    result=self.result,
                    first_feature=(first_feature if first_feature.id < second_feature.id else second_feature),
                    second_feature=(first_feature if first_feature.id >= second_feature.id else second_feature),
                    defaults={'redundancy': 0, 'weight': 0})

    def get_slices(self):
        slices = Slice.objects.filter(features__in=self.features, result=self.result)
        return {tuple([feature.name for feature in slice.features.all()]): ScoredSlices.from_dict(slice.definition) for slice in slices}

    def update_slices(self, new_slices: dict()):
        for feature_set, slices in new_slices.items():
            features = Feature.objects.filter(name__in=feature_set, dataset=self.target.dataset)
            Slice.objects.update_or_create(
                result=self.result,
                features=features,
                defaults={'definition': slices.to_dict()}
            )


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
    feature.is_categorical = (unique_values.size < 10)
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
    fourier_transformed_signal = ccwt.fft(feature_column)

    minimum_frequency = 0.001*len(feature_column)
    maximum_frequency = 0.5*len(feature_column)
    if frequency_base == 1.0:
        frequency_band = ccwt.frequency_band(height, maximum_frequency-minimum_frequency, minimum_frequency) # Linear
    else:
        minimum_octave = log(minimum_frequency)/log(frequency_base)
        maximum_octave = log(maximum_frequency)/log(frequency_base)
        frequency_band = ccwt.frequency_band(height, maximum_octave-minimum_octave, minimum_octave, frequency_base) # Exponential

    # Write into the spectrogram path
    filename = '{0}/spectrograms/{1}.png'.format(settings.MEDIA_ROOT, feature_id)
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as output_file:
        ccwt.render_png(output_file, ccwt.EQUIPOTENTIAL, 0.0, fourier_transformed_signal, frequency_band, width)

    Spectrogram.objects.create(
        feature=feature,
        width=width,
        height=height,
        image=filename
    )


@shared_task
def build_histogram(feature_id):
    feature = Feature.objects.get(pk=feature_id)

    # Only read column with that name
    dataframe = _get_dataframe(feature.dataset.id)

    bin_set = []
    bins, bin_edges = np.histogram(dataframe[feature.name], bins=50)
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
def downsample_feature(feature_id, sample_count=1000):
    feature = Feature.objects.get(pk=feature_id)

    dataframe = _get_dataframe(feature.dataset.id)
    feature_row = dataframe[feature.name]

    sample_set = []

    sampling = feature_row.groupby(np.arange(len(feature_row)) // (len(feature_row)//sample_count)).median()
    for idx, value in enumerate(sampling):
        # TODO: Test, order
        sample = Sample(
            feature=feature,
            value=value,
            order=idx
        )
        sample_set.append(sample)

    Sample.objects.bulk_create(sample_set)

    del sample_set, sampling


@shared_task
def calculate_hics(target_id, bivariate=True):
    target = Feature.objects.get(pk=target_id)
    dataframe = _get_dataframe(target.dataset.id)
    features = Feature.objects.filter(dataset=target.dataset).exclude(id=target.id).all()

    result = Result.objects.create(target=target)
    result_storage = DjangoHICSResultStorage(result=result, features=features)
    correlation = IncrementalCorrelation(data=dataframe, target=target.name, result_storage=result_storage,
                                         iterations=10, alpha=0.1, drop_discrete=False)

    if bivariate:
        correlation.update_bivariate_relevancies(runs=10)
    else:
        correlation.update_multivariate_relevancies(k=5, runs=100)

    result.status = Result.DONE
    result.save(update_fields=['status'])


@shared_task
def fixed_features_hics(target_id, fixed_feature_ids):
    target = Feature.objects.get(pk=target_id)
    dataframe = _get_dataframe(target.dataset.id)
    features = Feature.objects.filter(dataset=target.dataset).exclude(id=target.id).all()

    fixed_feature_names = [feature.name for feature in Feature.objects.filter(id__in=fixed_feature_ids).all()]  

    result = Result.objects.create(target=target)
    result_storage = DjangoHICSResultStorage(result=result, features=features)
    correlation = IncrementalCorrelation(data=dataframe, target=target.name, result_storage=result_storage,
                                         iterations=10, alpha=0.1, drop_discrete=False)

    correlation.update_multivariate_relevancies(fixed_feature_names, k=5, runs=10)

    result.status = Result.DONE
    result.save(update_fields=['status'])


@shared_task
def feature_set_hics(target_id, feature_ids):
    target = Feature.objects.get(pk=target_id)
    dataframe = _get_dataframe(target.dataset.id)
    features = Feature.objects.filter(dataset=target.dataset).exclude(id=target.id).all()

    feature_names = [feature.name for feature in Feature.objects.filter(id__in=feature_ids).all()]  

    result = Result.objects.create(target=target)
    result_storage = DjangoHICSResultStorage(result=result, features=features)
    correlation = IncrementalCorrelation(data=dataframe, target=target.name, result_storage=result_storage,
                                         iterations=10, alpha=0.1, drop_discrete=False)

    correlation.update_multivariate_relevancies(feature_names, k=len(feature_names), runs=5)

    result.status = Result.DONE
    result.save(update_fields=['status'])


@shared_task
def initialize_from_dataset(dataset_id):
    dataset = Dataset.objects.get(id=dataset_id)
    dataset.status = Dataset.PROCESSING #  TODO: Test
    dataset.save(update_fields=['status'])

    dataframe = _get_dataframe(dataset_id)

    # Only read first row for header
    headers = list(dataframe.columns.values)
    feature_ids = [Feature.objects.create(name=header, dataset=dataset).id for header in headers]

    # Chaining with Celery would be more beautiful...
    calculate_feature_statistics_subtasks = [
        calculate_feature_statistics.subtask(kwargs={'feature_id': feature_id}) for feature_id in
        feature_ids]
    build_spectrogram_subtasks = [build_spectrogram.subtask(kwargs={'feature_id': feature_id}) for
                                feature_id in feature_ids]
    build_histogram_subtasks = [build_histogram.subtask(kwargs={'feature_id': feature_id}) for
                                feature_id in feature_ids]
    downsample_feature_subtasks = [downsample_feature.subtask(kwargs={'feature_id': feature_id}) for
                                   feature_id in feature_ids]

    subtasks = calculate_feature_statistics_subtasks + build_spectrogram_subtasks + build_histogram_subtasks + downsample_feature_subtasks

    chord(subtasks)(initialize_from_dataset_processing_callback.subtask(kwargs={'dataset_id': dataset_id}))


@shared_task
def initialize_from_dataset_processing_callback(*args, **kwargs):
    dataset_id = kwargs['dataset_id']
    dataset = Dataset.objects.get(id=dataset_id)
    dataset.status = Dataset.DONE
    dataset.save(update_fields=['status'])


@shared_task
def calculate_conditional_distributions(target_id, feature_constraints) -> list:
    # TODO: Test
    target = Feature.objects.get(pk=target_id)

    logger.info(
        'Started for target {0} and features ranges/categories {1}'.format(target_id, feature_constraints))

    dataframe = _get_dataframe(dataset_id=target.dataset.id)

    # Convert feature ids to feature name for using it in dataframe
    for feature_constraint in feature_constraints:
        feature_name = Feature.objects.get(dataset_id=target.dataset.id,
                                           id=feature_constraint['feature']).name
        feature_constraint['feature'] = feature_name

    logger.info('Changed feature range to {0}'.format(feature_constraints))

    # Make filtering based on category or range
    filter_list = np.array([True] * len(dataframe))
    for ftr in feature_constraints:
        if 'range' in ftr:
            filter_list = np.logical_and(dataframe[ftr['feature']] >= ftr['range']['from_value'], filter_list)
            filter_list = np.logical_and(dataframe[ftr['feature']] <= ftr['range']['to_value'], filter_list)

        elif 'categories' in ftr:
            filter_list = np.logical_and(dataframe[ftr['feature']].isin(ftr['categories']), filter_list)

    # Calculate conditional probabilites based on filtering
    values, counts = np.unique(dataframe.loc[filter_list, target.name], return_counts=True)
    probabilities = counts / filter_list.sum()

    # Convert to result dict
    result = [{'value': float(probs[0]), 'probability': probs[1]} for probs in zip(values, probabilities)]

    logger.info('Result: {0}'.format(result))

    return result


@periodic_task(run_every=(crontab(minute=15)), ignore_result=True)
def remove_unused_dataframes(max_delta=3600):
    """
    Delete all in-memory information of a dataset if it wasn't accessed in the last max_delta seconds

    :param max_delta: Maximum delta in seconds
    """
    dataframe_lock.acquire()

    min_time = time() - max_delta
    for dataset_id, timestamp in dataframe_last_access.items():
        if timestamp < min_time:
            del dataframe_last_access[dataset_id]
            del dataframe_columns[dataset_id]
            sa.delete(dataset_id)

    dataframe_lock.release()
