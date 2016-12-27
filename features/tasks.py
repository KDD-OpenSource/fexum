from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Histogram, Bin
from features.algorithms import submitter
import json
import logging


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

    feature.min = np.amin(feature_col)
    feature.max = np.amax(feature_col)
    feature.mean = np.mean(feature_col)
    feature.variance = np.nanvar(feature_col)

    feature.save()


@shared_task
def build_histogram(path, feature_name):
    # Only read column with that name
    dataframe = pd.read_csv(path, usecols=[feature_name])

    feature = Feature.objects.get(name=feature_name)
    histogram = Histogram.objects.create(feature=feature)

    bins, bin_edges = np.histogram(dataframe[feature_name], bins='auto')
    for bin_index, bin_value in enumerate(bins):
        from_value = bin_edges[bin_index]
        to_value = bin_edges[bin_index + 1]
        Bin.objects.create(histogram=histogram, from_value=from_value, to_value=to_value,
                           count=bin_value)


def rar_callback(parsed):
        for feature_result in parsed['results']['feature_ranking']:
            feature = Feature.objects.get(name=feature_result['name'])
            feature.rank = feature_result['rank']
            feature.save()
            print("Updating feature " + feature_result['name'] + " to rank " + str(feature_result['rank']))


@shared_task
def calculate_rar(path, target_index):
    submitter.execJob("java -jar assets/rar-mfs_1.0.1.jar csv " + path + " -t " + str(target_index), submitter.Algorithms['rar'])
