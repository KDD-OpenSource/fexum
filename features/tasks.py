from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample, Dataset, RarResult, \
    Redundancy, Relevancy
from subprocess import Popen, PIPE
import json
from django.db.models.signals import post_save, pre_save
from celery.task import chord
from celery.utils.log import get_task_logger
from multiprocessing import Manager
import SharedArray as sa


logger = get_task_logger(__name__)

# Locking of shared memory
manager = Manager()
dataframe_columns = manager.dict()
dataframe_lock = manager.Lock()

# Fix bindings in celery context
from features.bindings import RarResultBinding, DatasetBinding
DatasetBinding.register()
RarResultBinding.register()


def _get_dataset_and_file(dataset_id) -> (Dataset, str):
    dataset = Dataset.objects.get(pk=dataset_id)
    filename = dataset.content.path
    return dataset, filename


def _get_dataframe(dataset_id: str) -> pd.DataFrame:
    dataframe_lock.acquire()

    dataset_id = str(dataset_id)

    try:
        shared_array = sa.attach('shm://{0}'.format(dataset_id))
        columns = dataframe_columns[dataset_id]

        logger.info('Cache hit for dataset {0}'.format(dataset_id))
    except FileNotFoundError:
        logger.info('Cache miss for dataset {0}'.format(dataset_id))

        # Fetch dataset from disk and put it into RAM
        _, filename = _get_dataset_and_file(dataset_id=dataset_id)
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


def _parse_and_save_rar_results(target: Feature, rar_result_dict: dict):
    # The Results Model should separate RaR results from different runs
    # TODO: Test and refactor status
    rar_result = RarResult.objects.create(target=target, status=RarResult.EMPTY)

    for redundancy_data in rar_result_dict['redundancies']:
        first_feature = Feature.objects.get(dataset=target.dataset,
                                            name=redundancy_data['feature1'])
        second_feature = Feature.objects.get(dataset=target.dataset,
                                             name=redundancy_data['feature2'])

        Redundancy.objects.update_or_create(
            rar_result=rar_result,
            first_feature=(first_feature if first_feature.id < second_feature.id else second_feature),
            second_feature=(first_feature if first_feature.id >= second_feature.id else second_feature),
            defaults={'redundancy': redundancy_data['redundancy'], 'weight': redundancy_data['weight']}
        )

    # Parse and save results
    for idx, relevancy_data in enumerate(rar_result_dict['relevancies']):
        feature = Feature.objects.get(dataset=target.dataset, name=relevancy_data['name'])
        relevancy = Relevancy.objects.create(
            feature=feature,
            rank=idx,
            relevancy=relevancy_data['result']['score'],
            rar_result=rar_result
        )

        for slice_data in relevancy_data['result']['scoredBlocks']:
            Slice.objects.create(
                relevancy=relevancy,
                marginal_distribution=slice_data['normalizedMarginalDistribution'],
                conditional_distribution=slice_data['normalizedConditionalDistribution'],
                deviation=slice_data['deviation'],
                frequency=slice_data['frequency'],
                from_value=slice_data['featureRanges'][0]['start'],
                to_value=slice_data['featureRanges'][0]['end']
            )
    # Test status
    rar_result.status = RarResult.DONE
    rar_result.save(update_fields=['status'])


@shared_task
def calculate_rar(target_id, precomputed_data=None):
    target = Feature.objects.get(pk=target_id)
    _, filename = _get_dataset_and_file(target.dataset.id)

    # TODO: Add test

    # Only execute rar if don't insert data manually
    if precomputed_data is not None:
        # TODO: Add test
        results = precomputed_data
        _parse_and_save_rar_results(target=target, rar_result_dict=results)
        return

    # Return if rar was already calculated for a specific target
    if RarResult.objects.filter(target=target).exists():
        # Manually trigger notifications
        rar_result = RarResult.objects.filter(target=target).first()
        pre_save.send(RarResult, instance=rar_result)
        post_save.send(RarResult, instance=rar_result, created=False)

        return

    # Execute Rar
    JAR_FILE = '/assets/rar-mfs.jar'
    process = Popen([
        'java',
        '-d64',
        '-Xms8g',
        '-Xmx32g',
        '-jar', JAR_FILE,
        'csv',
        '--samples', '100',
        '--subsetSize', '5',
        '--nonorm', filename,
        '--hics',
        '--targetName', target.name],
        stdout=PIPE)
    raw_output, err = process.communicate()
    results = json.loads(raw_output)
    _parse_and_save_rar_results(target=target, rar_result_dict=results)


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
    build_histogram_subtasks = [build_histogram.subtask(kwargs={'feature_id': feature_id}) for
                                feature_id in feature_ids]
    downsample_feature_subtasks = [downsample_feature.subtask(kwargs={'feature_id': feature_id}) for
                                   feature_id in feature_ids]

    subtasks = calculate_feature_statistics_subtasks + build_histogram_subtasks + downsample_feature_subtasks

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
