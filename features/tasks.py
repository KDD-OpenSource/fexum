from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample, Dataset, RedundancyResult, RelevancyResult
from subprocess import Popen, PIPE
import json
from math import ceil
from django.db.models.signals import post_save, pre_save


def _get_dataset_and_file(dataset_id) -> (Dataset, str):
    dataset = Dataset.objects.get(pk=dataset_id)
    filename = dataset.content.path
    return dataset, filename


@shared_task
def calculate_feature_statistics(feature_id):
    feature = Feature.objects.get(pk=feature_id)
    _, filename = _get_dataset_and_file(feature.dataset.id)

    dataframe = pd.read_csv(filename, usecols=[feature.name])
    feature_col = dataframe[feature.name]

    feature.min = np.amin(feature_col).item()
    feature.max = np.amax(feature_col).item()
    feature.mean = np.mean(feature_col).item()
    feature.variance = np.nanvar(feature_col).item()
    # TODO: Test
    feature.is_categorical = np.unique(feature_col).size <= 10

    feature.save()


@shared_task
def build_histogram(feature_id):
    feature = Feature.objects.get(pk=feature_id)
    _, filename = _get_dataset_and_file(feature.dataset.id)

    # Only read column with that name
    dataframe = pd.read_csv(filename, usecols=[feature.name])

    bins, bin_edges = np.histogram(dataframe[feature.name], bins='auto')
    for bin_index, bin_value in enumerate(bins):
        from_value = bin_edges[bin_index]
        to_value = bin_edges[bin_index + 1]
        Bin.objects.create(feature=feature, from_value=from_value, to_value=to_value,
                           count=bin_value)


@shared_task
def downsample_feature(feature_id, sample_rate=32):
    feature = Feature.objects.get(pk=feature_id)
    _, filename = _get_dataset_and_file(feature.dataset.id)

    dataframe = pd.read_csv(filename, usecols=[feature.name])
    feature_row = dataframe[feature.name]

    sampling = feature_row.groupby(np.arange(len(feature_row)) // sample_rate).median()
    for value in sampling:
        Sample.objects.create(feature=feature, value=value)


@shared_task
def calculate_rar(target_id, precomputed_data=None):
    target = Feature.objects.get(pk=target_id)
    _, filename = _get_dataset_and_file(target.dataset.id)

    # Fix bindings in celery context
    from features.bindings import RelevancyResultBinding, RedundancyResultBinding
    RelevancyResultBinding.register()
    RedundancyResultBinding.register()

    # TODO: Add test
    # Return if rar was already calculated for a specific target
    if RelevancyResult.objects.filter(target=target).exists():
        # Manually trigger notifications

        relevancy_results = RelevancyResult.objects.filter(target=target)
        for relevancy_result in relevancy_results:
            pre_save.send(RelevancyResult, instance=relevancy_result)
            post_save.send(RelevancyResult, instance=relevancy_result, created=False)

        redundancy_results = RedundancyResult.objects.filter(first_feature=target)
        for redundancy_result in redundancy_results:
            pre_save.send(RedundancyResult, instance=redundancy_result)
            post_save.send(RedundancyResult, instance=redundancy_result, created=False)

        return

    # Only execute rar if don't insert data manually
    if precomputed_data is not None:
        # TODO: Add test
        results = precomputed_data
    else:
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

    for redundancy_data in results['redundancies']:
        first_feature = Feature.objects.get(dataset=target.dataset,
                                            name=redundancy_data['feature1'])
        second_feature = Feature.objects.get(dataset=target.dataset,
                                             name=redundancy_data['feature2'])

        RedundancyResult.objects.update_or_create(
            first_feature=(first_feature if first_feature.id < second_feature.id else second_feature),
            second_feature=(first_feature if first_feature.id >= second_feature.id else second_feature),
            defaults={'redundancy': redundancy_data['redundancy']}
        )

    # Parse and save results
    for idx, relevancy_data in enumerate(results['relevancies']):
        feature = Feature.objects.get(dataset=target.dataset, name=relevancy_data['name'])
        relevancy_result = RelevancyResult.objects.create(
            feature=feature,
            target=target,
            rank=idx,
            relevancy=relevancy_data['result']['score']
        )

        for slice_data in relevancy_data['result']['scoredBlocks']:
            Slice.objects.create(
                relevancy_result = relevancy_result,
                marginal_distribution = slice_data['normalizedMarginalDistribution'],
                conditional_distribution = slice_data['normalizedConditionalDistribution'],
                deviation = slice_data['deviation'],
                frequency = slice_data['frequency'],
                from_value = slice_data['featureRanges'][0]['start'],
                to_value = slice_data['featureRanges'][0]['end']
            )

    
@shared_task
def initialize_from_dataset(dataset_id):
    dataset, filename = _get_dataset_and_file(dataset_id)

    # Only read first row for header
    dataframe = pd.read_csv(filename, nrows=1)
    headers = list(dataframe.columns.values)
    for header in headers:
        feature = Feature.objects.create(name=header, dataset=dataset)

        # Chaining with Celery would be more beautiful...
        calculate_feature_statistics.delay(feature_id=feature.id)
        build_histogram.delay(feature_id=feature.id)
        downsample_feature.delay(feature_id=feature.id)


@shared_task
def calculate_arbitary_slices(target_id, ranges_feature_ids):
    target = Feature.objects.get(pk=target_id)
    dataset, filename = _get_dataset_and_file(target.dataset.id)

    # Convert feature ids to feature name for using it in dataframe
    feature_ranges = [{'feature': Feature.objects.get(dataset=dataset, id=ranges_feature_id['feature']),
                       'from_value': ranges_feature_id['from_value'],
                       'to_value': ranges_feature_id['to_value']} for ranges_feature_id in ranges_feature_ids]
    feature_names = [feature_range['feature'] for feature_range in feature_ranges]

    dataframe = pd.read_csv(filename, usecols=feature_names + [target.name])

    # Make filtering
    filter_array = np.array([True] * len(dataframe))
    for ftr in feature_ranges:
        filter_array = np.logical_and(dataframe[ftr['feature']] >= ftr['from_value'], filter_array)
        filter_array = np.logical_and(dataframe[ftr['feature']] <= ftr['to_value'], filter_array)
    values, counts = np.unique(dataframe.loc[filter_array, target_id], return_counts=True)
    probabilies = counts / filter_array.sum()

    # Convert to result dict
    result = [{'value': value_probabilies[0],
               'probability': value_probabilies[1]} for value_probabilies in zip(values, probabilies)]

    return result
