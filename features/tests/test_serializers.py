from django.test import TestCase
from features.tests.factories import SampleFactory, FeatureFactory, BinFactory, SliceFactory
from features.serializers import FeatureSerializer, BinSerializer, \
    SliceSerializer, SampleSerializer, TargetSerializer
from features.tests.factories import FeatureFactory, BinFactory, SliceFactory, TargetFactory
from decimal import Decimal


class TestFeatureSerializer(TestCase):
    def test_serialize_one(self):
        feature = FeatureFactory()
        serializer = FeatureSerializer(instance=feature)
        data = serializer.data

        self.assertEqual(data.pop('name'), feature.name)
        self.assertEqual(data.pop('relevancy'), feature.relevancy)
        self.assertEqual(data.pop('redundancy'), feature.redundancy)
        self.assertEqual(data.pop('rank'), feature.rank)
        self.assertEqual(data.pop('min'), feature.min)
        self.assertEqual(data.pop('max'), feature.max)
        self.assertEqual(data.pop('mean'), feature.mean)
        self.assertEqual(data.pop('variance'), feature.variance)
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
        self.assertEqual(Decimal(data.pop('significance')), a_slice.significance)
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


class TestTargetSerializer(TestCase):
    def test_serialize_one(self):
        target = TargetFactory()
        serializer = TargetSerializer(instance=target)
        data = serializer.data
        feature_data = FeatureSerializer(instance=target.feature).data

        self.assertEqual(data.pop('feature'), feature_data)
        self.assertEqual(len(data), 0)
