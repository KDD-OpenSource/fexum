from django.test import TestCase
from features.serializers import FeatureSerializer, BinSerializer, ExperimentTargetSerializer, \
    SliceSerializer, SampleSerializer, DatasetSerializer, ExperimentSerializer, \
    RedundancySerializer, RelevancySerializer, \
    ConditionalDistributionRequestSerializer, ConditionalDistributionResultSerializer, \
    FeatureSliceSerializer
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    DatasetFactory, SampleFactory, ExperimentFactory, RelevancyFactory, RedundancyFactory
from decimal import Decimal
from rest_framework.exceptions import ValidationError


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


class TestSliceSerializer(TestCase):
    def test_serialize_one(self):
        a_slice = SliceFactory()
        serializer = SliceSerializer(instance=a_slice)
        data = serializer.data

        self.assertEqual(Decimal(data.pop('from_value')), a_slice.from_value)
        self.assertEqual(Decimal(data.pop('to_value')), a_slice.to_value)
        self.assertEqual(Decimal(data.pop('deviation')), a_slice.deviation)
        self.assertEqual(Decimal(data.pop('frequency')), a_slice.frequency)
        self.assertEqual(data.pop('marginal_distribution'), a_slice.marginal_distribution)
        self.assertEqual(data.pop('conditional_distribution'), a_slice.conditional_distribution)
        self.assertEqual(len(data), 0)


class TestSampleSerializer(TestCase):
    def test_serialize_one(self):
        sample = SampleFactory()
        serializer = SampleSerializer(instance=sample)
        data = serializer.data

        self.assertEqual(Decimal(data.pop('value')), sample.value)
        self.assertEqual(Decimal(data.pop('order')), sample.order)
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
        relevancy = RelevancyFactory()
        serializer = RelevancySerializer(instance=relevancy)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(relevancy.id))
        self.assertEqual(data.pop('feature'), relevancy.feature.id)
        self.assertEqual(data.pop('relevancy'), relevancy.relevancy)
        self.assertEqual(data.pop('rank'), relevancy.rank)
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


class TestFeatureSliceSerializer(TestCase):
    def test_serialize_one(self):
        slice = SliceFactory()
        serializer = FeatureSliceSerializer(instance=slice)

        data = serializer.data
        self.assertAlmostEqual(data.pop('deviation'), slice.deviation)
        self.assertAlmostEqual(data.pop('frequency'), slice.frequency)
        first_feature = data.pop('features').pop(0)
        self.assertEqual(len(data), 0)
        self.assertEqual(first_feature.pop('feature'), slice.relevancy.feature.id)
        self.assertAlmostEqual(first_feature.pop('from_value'), slice.from_value)
        self.assertAlmostEqual(first_feature.pop('to_value'), slice.to_value)


class TestConditionalDistributionRequestSerializer(TestCase):
    def test_deserialize_one(self):
        feature = FeatureFactory()

        # Test that we can only specify one condition
        data = {'feature': feature.id, 'range': {'from_value': 0, 'to_value': 1}, 'categories':[4.0, 3]}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid, raise_exception=True)
        self.assertEqual(serializer.errors, {'non_field_errors': ['Specify either a range or categories.']})

        # Test for range
        data = {'feature': feature.id, 'range': {'from_value': 0, 'to_value': 1}}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(dict(serializer.validated_data), {'feature': feature, 'range': data['range']})

        # Test for categories
        data = {'feature': feature.id, 'categories':[4.0, 3.0]}
        serializer = ConditionalDistributionRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(dict(serializer.validated_data), {'feature': feature, 'categories': data['categories']})


class TestConditionalDistributionResultSerializer(TestCase):
    def test_serialize_one(self):
        data = {'value': 1, 'probability': 1}
        serializer = ConditionalDistributionResultSerializer(data=data)
        self.assertTrue(serializer.is_valid(raise_exception=True))
        self.assertEqual(serializer.data, data)