from django.test import TestCase
from features.tests.factories import FeatureFactory, BucketFactory, HistogramFactory, SliceFactory
from features.serializers import FeatureSerializer, BucketSerializer, HistogramSerializer, SliceSerializer
from decimal import Decimal

class TestFeatureSerializer(TestCase):
    def test_serialize_one(self):
        feature = FeatureFactory()
        serializer = FeatureSerializer(instance=feature)
        data = serializer.data

        self.assertEqual(data.pop('id'), feature.id)
        self.assertEqual(data.pop('name'), feature.name)
        self.assertEqual(data.pop('relevancy'), feature.relevancy)
        self.assertEqual(data.pop('redundancy'), feature.redundancy)
        self.assertEqual(data.pop('rank'), feature.rank)
        self.assertEqual(data.pop('is_target'), feature.is_target)
        self.assertEqual(len(data), 0)


class TestHistogramSerializer(TestCase):
    def test_serialize_one(self):
        bucket = BucketFactory()
        histogram = bucket.histogram
        serializer = HistogramSerializer(instance=histogram)
        data = serializer.data

        self.assertEqual(data.pop('id'), histogram.id)
        self.assertEqual(data.pop('buckets'), [{
            'from_value': bucket.from_value,
            'to_value': bucket.to_value,
            'count': bucket.count
        }])
        self.assertEqual(len(data), 0)


class TestBucketSerializer(TestCase):
    def test_serialize_one(self):
        bucket = BucketFactory()
        serializer = BucketSerializer(instance=bucket)
        data = serializer.data

        self.assertEqual(Decimal(data.pop('from_value')), bucket.from_value)
        self.assertEqual(Decimal(data.pop('to_value')), bucket.to_value)
        self.assertEqual(data.pop('count'), bucket.count)
        self.assertEqual(len(data), 0)


class TestSliceSerializer(TestCase):
    def test_serialize_one(self):
        a_slice = SliceFactory()
        serializer = SliceSerializer(instance=a_slice)
        data = serializer.data

        self.assertEqual(Decimal(data.pop('from_value')), a_slice.from_value)
        self.assertEqual(Decimal(data.pop('to_value')), a_slice.to_value)
        self.assertEqual(data.pop('marginal_distribution'), a_slice.marginal_distribution)
        self.assertEqual(data.pop('conditional_distribution'), a_slice.conditional_distribution)
        self.assertEqual(len(data), 0)
