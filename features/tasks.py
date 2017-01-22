from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample, Dataset, RarResult
from subprocess import Popen, PIPE
import json
from channels import Group
from math import ceil


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
def downsample_feature(feature_id, sample_count=1000):
    feature = Feature.objects.get(pk=feature_id)
    _, filename = _get_dataset_and_file(feature.dataset.id)

    dataframe = pd.read_csv(filename, usecols=[feature.name])

    feature_rows = dataframe[feature.name]
    count = feature_rows.count()
    sampling = feature_rows[::int(ceil(count/sample_count))]

    for value in sampling:
        Sample.objects.create(feature=feature, value=value)


@shared_task
def calculate_rar(target_id):
    target = Feature.objects.get(pk=target_id)
    _, filename = _get_dataset_and_file(target.dataset.id)

    # Return if rar was already calculated for a specific target
    if RarResult.objects.filter(target=target).exists():
        return

    # Execute Rar
    JAR_FILE = '/assets/rar-mfs.jar'
    process = Popen(
        ['java', '-d64', '-Xms8g', '-Xmx32g', '-jar', JAR_FILE, 'csv', '--samples', '100', '--subsetSize', '5', '--nonorm', filename,
         '--hics'], stdout=PIPE)
    raw_output, err = process.communicate()
    results = json.loads(raw_output)

    # Parse and save results
    for idx, feature_data in enumerate(results):
        feature = Feature.objects.get(dataset=target.dataset, name=feature_data['name'])
        rar_result = RarResult.objects.create(
            feature=feature,
            target=target,
            rank=idx,
            relevancy=feature_data['result']['score']
        )

        for slice_data in feature_data['result']['scoredBlocks']:
            slice_obj = Slice()
            slice_obj.rar_result = rar_result
            slice_obj.feature = Feature.objects.get(name=feature_data['name'])
            slice_obj.marginal_distribution = slice_data['normalizedMarginalDistribution']
            slice_obj.conditional_distribution = slice_data['normalizedConditionalDistribution']
            slice_obj.deviation = slice_data['deviation']
            slice_obj.frequency = slice_data['frequency']
            slice_obj.significance = slice_data['significance']
            slice_obj.from_value = slice_data['featureRanges'][0]['start']
            slice_obj.to_value = slice_data['featureRanges'][0]['end']
            slice_obj.save()

    
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
