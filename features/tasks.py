from __future__ import absolute_import, unicode_literals
from celery import shared_task
import pandas as pd
import numpy as np
from features.models import Feature, Histogram, Bin


@shared_task
def initialize_from_dataset(path):
    # Only read first row for header
    dataframe = pd.read_csv(path, nrows=1)
    headers = list(dataframe.columns.values)
    for header in headers:
        Feature.objects.create(name=header)


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
