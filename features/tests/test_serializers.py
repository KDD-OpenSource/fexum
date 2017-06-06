from decimal import Decimal

from django.test import TestCase
from rest_framework.exceptions import ValidationError

from features.serializers import FeatureSerializer, BinSerializer, ExperimentTargetSerializer, \
    DatasetSerializer, ExperimentSerializer, RedundancySerializer, RelevancySerializer, \
    ConditionalDistributionRequestSerializer, \
    SpectrogramSerializer, CalculationSerializer
from features.tests.factories import FeatureFactory, BinFactory, DatasetFactory, ExperimentFactory, \
    RelevancyFactory, RedundancyFactory, SpectrogramFactory, \
    CalculationFactory


class TestFeatureSerializer(TestCase):
    def test_serialize_one(self):
        feature = FeatureFactory()
        serializer = FeatureSerializer(instance=feature)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(feature.id))
        self.assertEqual(data.pop('name'), feature.name)
        self.assertEqual(data.pop('min'), feature.min)
        self.assertEqual(data.pop('max'), feature.max)
        self.assertEqual(data.pop('mean'), feature.mean)
        self.assertEqual(data.pop('variance'), feature.variance)
        self.assertEqual(data.pop('is_categorical'), feature.is_categorical)
        self.assertEqual(data.pop('categories'), feature.categories)
        self.assertEqual(len(data), 0)


class TestBinSerializer(TestCase):
    def test_serialize_one(self):
        bin = BinFactory()
        serializer = BinSerializer(instance=bin)
        data = serializer.data

        self.assertEqual(Decimal(data.pop('from_value')), bin.from_value)
        self.assertEqual(Decimal(data.pop('to_value')), bin.to_value)
        self.assertEqual(data.pop('count'), bin.count)
        self.assertEqual(len(data), 0)


class TestDatasetSerializer(TestCase):
    def test_serialize_one(self):
        dataset = DatasetFactory()
        serializer = DatasetSerializer(instance=dataset)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(dataset.id))
        self.assertEqual(data.pop('name'), dataset.name)
        self.assertEqual(data.pop('status'), dataset.status)
        self.assertEqual(len(data), 0)


class TestExperimentSerializer(TestCase):
    def test_serialize_one(self):
        experiment = ExperimentFactory()
        serializer = ExperimentSerializer(instance=experiment)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(experiment.id))
        self.assertEqual(data.pop('dataset'), experiment.dataset.id)
        self.assertEqual(data.pop('target'), experiment.target.id)
        self.assertEqual(len(data), 0)


class TestRelevancySerializer(TestCase):
    def test_serialize_one(self):
        features = [FeatureFactory()]
        relevancy = RelevancyFactory(features=features)
        serializer = RelevancySerializer(instance=relevancy)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(relevancy.id))
        self.assertEqual(data.pop('features'), [feature.id for feature in features])
        self.assertEqual(data.pop('relevancy'), relevancy.relevancy)
        self.assertEqual(data.pop('iteration'), relevancy.iteration)
        self.assertEqual(len(data), 0)


class TestRedundancySerializer(TestCase):
    def test_serialize_one(self):
        redundancy = RedundancyFactory()
        serializer = RedundancySerializer(instance=redundancy)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(redundancy.id))
        self.assertEqual(data.pop('first_feature'), redundancy.first_feature.id)
        self.assertEqual(data.pop('second_feature'), redundancy.second_feature.id)
        self.assertEqual(data.pop('redundancy'), redundancy.redundancy)
        self.assertEqual(data.pop('weight'), redundancy.weight)
        self.assertEqual(len(data), 0)


class TestExperimentTargetSerializer(TestCase):
    def test_serialize_one(self):
        experiment = ExperimentFactory()
        serializer = ExperimentTargetSerializer(instance=experiment)
        data = serializer.data

        self.assertEqual(data.pop('target'), experiment.target.id)
        self.assertEqual(len(data), 0)


class TestConditionalDistributionRequestSerializer(TestCase):
    def test_deserialize_one(self):
        feature = FeatureFactory()

        # Test that we can only specify one condition
        data = {'feature': feature.id, 'range': {'from_value': 0, 'to_value': 1}, 'categories': [4.0, 3]}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)
        self.assertEqual(serializer.errors, {'non_field_errors': ['Specify either a range or categories.']})

        # Test for range
        data = {'feature': feature.id, 'range': {'from_value': 0, 'to_value': 1}}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        print(dict(serializer.validated_data))
        self.assertEqual(dict(serializer.validated_data), {'feature': feature, 'range': data['range']})

        # Test for categories
        data = {'feature': feature.id, 'categories': [4.0, 3.0]}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(dict(serializer.validated_data), {'feature': feature, 'categories': data['categories']})

"""
class TestConditionalDistributionResultSerializer(TestCase):
    def test_serialize_one(self):
        data = {'value': 1, 'probability': 1}
        serializer = ConditionalDistributionResultSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        self.assertEqual(serializer.data, data)
"""


class TestSpectrogramSerializer(TestCase):
    def test_serialize_one(self):
        spectrogram = SpectrogramFactory()
        serializer = SpectrogramSerializer(instance=spectrogram)
        data = serializer.data

        self.assertEqual(data.pop('width'), spectrogram.width)
        self.assertEqual(data.pop('height'), spectrogram.height)
        self.assertEqual(data.pop('image_url'), '/media/spectrograms/{0}.png'.format(spectrogram.feature.id))
        self.assertEqual(len(data), 0)


class TestCalculationSerializer(TestCase):
    def test_serialize_one(self):
        calculation = CalculationFactory()
        serializer = CalculationSerializer(instance=calculation)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(calculation.id))
        self.assertEqual(data.pop('max_iteration'), calculation.max_iteration)
        self.assertEqual(data.pop('current_iteration'), calculation.current_iteration)
        self.assertEqual(len(data), 0)