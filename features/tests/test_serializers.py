from django.test import TestCase
from features.serializers import FeatureSerializer, BinSerializer, SessionTargetSerializer, \
    SliceSerializer, SampleSerializer, DatasetSerializer, SessionSerializer, \
    RedundancyResultSerializer, RelevancyResultSerializer
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, \
    DatasetFactory, SampleFactory, SessionFactory, RedundancyResultFactory, RelevancyResultFactory
from decimal import Decimal


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
        self.assertEqual(len(data), 0)


class TestDatasetSerializer(TestCase):
    def test_serialize_one(self):
        dataset = DatasetFactory()
        serializer = DatasetSerializer(instance=dataset)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(dataset.id))
        self.assertEqual(data.pop('name'), dataset.name)
        self.assertEqual(len(data), 0)


class TestSessionSerializer(TestCase):
    def test_serialize_one(self):
        session = SessionFactory()
        serializer = SessionSerializer(instance=session)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(session.id))
        self.assertEqual(data.pop('dataset'), session.dataset.id)
        self.assertEqual(data.pop('target'), session.target.id)
        self.assertEqual(len(data), 0)


class TestRelevancyResultsSerializer(TestCase):
    def test_serialize_one(self):
        relevancy_result = RelevancyResultFactory()
        serializer = RelevancyResultSerializer(instance=relevancy_result)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(relevancy_result.id))
        self.assertEqual(data.pop('feature'), relevancy_result.feature.id)
        self.assertEqual(data.pop('relevancy'), relevancy_result.relevancy)
        self.assertEqual(data.pop('rank'), relevancy_result.rank)
        self.assertEqual(data.pop('target'), relevancy_result.target.id)
        self.assertEqual(len(data), 0)


class TestRedundancyResultsSerializer(TestCase):
    def test_serialize_one(self):
        redundancy_result = RedundancyResultFactory()
        serializer = RedundancyResultSerializer(instance=redundancy_result)
        data = serializer.data

        self.assertEqual(data.pop('id'), str(redundancy_result.id))
        self.assertEqual(data.pop('first_feature'), redundancy_result.first_feature.id)
        self.assertEqual(data.pop('second_feature'), redundancy_result.second_feature.id)
        self.assertEqual(data.pop('redundancy'), redundancy_result.redundancy)
        self.assertEqual(len(data), 0)


class TestSessionTargetSerializer(TestCase):
    def test_serialize_one(self):
        session = SessionFactory()
        serializer = SessionTargetSerializer(instance=session)
        data = serializer.data

        self.assertEqual(data.pop('target'), session.target.id)
        self.assertEqual(len(data), 0)

