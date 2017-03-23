from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample, Dataset, Result, \
    Redundancy, Relevancy
from celery.task import chord
from celery.utils.log import get_task_logger
from multiprocessing import Manager
import SharedArray as sa
from hics.incremental_correlation import IncrementalCorrelation
from hics.result_storage import AbstractResultStorage
from hics.scored_slices import ScoredSlices
from features.bindings import ResultBinding, DatasetBinding


logger = get_task_logger(__name__)

# Locking of shared memory
manager = Manager()
dataframe_columns = manager.dict()
dataframe_lock = manager.Lock()

# Fix bindings in celery context
DatasetBinding.register()
ResultBinding.register()


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

        dataframe_lock.release()

        dataframe = pd.DataFrame(shared_array, columns=columns)

        logger.info('Cache hit for dataset {0}'.format(dataset_id))
    except FileNotFoundError:
        logger.info('Cache miss for dataset {0}'.format(dataset_id))

        # Fetch dataset from disk and put it into RAM
        _, filename = _get_dataset_and_file(dataset_id=dataset_id)
        dataframe = pd.read_csv(filename)
        shared_array = sa.create('shm://{0}'.format(dataset_id), dataframe.shape)
        shared_array[:] = dataframe.values
        dataframe_columns[dataset_id] = dataframe.columns

        dataframe_lock.release()

        logger.info('Cache save for dataset {0}'.format(dataset_id))

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


@shared_task
def build_histogram(feature_id):
    feature = Feature.objects.get(pk=feature_id)

    # Only read column with that name
    dataframe = _get_dataframe(feature.dataset.id)

    bin_set = []
    bins, bin_edges = np.histogram(dataframe[feature.name], bins='auto')
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
        correlation.update_bivariate_relevancies(runs=1)
        correlation.update_bivariate_relevancies(runs=1)
    else:
        raise NotImplementedError()

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





