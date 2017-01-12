from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Bin, Slice, Sample
from subprocess import Popen, PIPE
import json
from features.channels import GROUP_NAME
from channels import Group
from math import ceil


@shared_task
def initialize_from_dataset(path):
    # Only read first row for header
    dataframe = pd.read_csv(path, nrows=1)
    headers = list(dataframe.columns.values)
    for header in headers:
        Feature.objects.create(name=header)


@shared_task
def calculate_feature_statistics(path, feature_name):
    dataframe = pd.read_csv(path, usecols=[feature_name])
    feature_col = dataframe[feature_name]

    feature = Feature.objects.get(name=feature_name)

    feature.min = np.amin(feature_col).item()
    feature.max = np.amax(feature_col).item()
    feature.mean = np.mean(feature_col).item()
    feature.variance = np.nanvar(feature_col).item()

    feature.save()


@shared_task
def build_histogram(path, feature_name):
    # Only read column with that name
    dataframe = pd.read_csv(path, usecols=[feature_name])

    feature = Feature.objects.get(name=feature_name)

    bins, bin_edges = np.histogram(dataframe[feature_name], bins='auto')
    for bin_index, bin_value in enumerate(bins):
        from_value = bin_edges[bin_index]
        to_value = bin_edges[bin_index + 1]
        Bin.objects.create(feature=feature, from_value=from_value, to_value=to_value,
                           count=bin_value)


@shared_task
def downsample_feature(path, feature_name, sample_count):
    dataframe = pd.read_csv(path, usecols=[feature_name])

    feature = Feature.objects.get(name=feature_name)
    feature_rows = dataframe[feature_name]
    count = feature_rows.count()
    sampling = feature_rows[::int(ceil(count/sample_count))]

    for value in sampling:
        Sample.objects.create(feature=feature, value=value)


@shared_task
def calculate_rar(path):
    JAR_FILE = '/assets/rar-mfs.jar'
    process = Popen(
        ['java', '-d64', '-Xms8g', '-Xmx32g', '-jar', JAR_FILE, 'csv', '--samples', '100', '--subsetSize', '5', '--nonorm', path,
         '--hics'], stdout=PIPE)
    raw_output, err = process.communicate()
    results = json.loads(raw_output)

    for idx, feature_data in enumerate(results):
        feature = Feature.objects.get(name=feature_data['name'])
        feature.rank = idx
        feature.relevancy = feature_data['result']['score']
        feature.save()

        for slice_data in feature_data['result']['scoredBlocks']:
            slice_obj = Slice()
            slice_obj.feature = Feature.objects.get(name=feature_data['name'])
            slice_obj.marginal_distribution = slice_data['normalizedMarginalDistribution']
            slice_obj.conditional_distribution = slice_data['normalizedConditionalDistribution']
            slice_obj.deviation = slice_data['deviation']
            slice_obj.frequency = slice_data['frequency']
            slice_obj.significance = slice_data['significance']
            slice_obj.from_value = slice_data['featureRanges'][0]['start']
            slice_obj.to_value = slice_data['featureRanges'][0]['end']
            slice_obj.save()

    # TODO: Send message on save signal, not here?
    Group(GROUP_NAME).send({'text': json.dumps({'event_name': 'relevancy-update', 'payload': {}})})
