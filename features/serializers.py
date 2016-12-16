from rest_framework.serializers import ModelSerializer, JSONField, RelatedField
from features.models import Feature, Bucket, Histogram, Slice


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'relevancy', 'redundancy', 'rank', 'is_target')


class BucketSerializer(ModelSerializer):
    class Meta:
        model = Bucket
        fields = ('from_value', 'to_value', 'count')


class HistogramSerializer(ModelSerializer):
    buckets = BucketSerializer(read_only=True, many=True)

    class Meta:
        model = Histogram
        fields = ('id', 'buckets')


class SliceSerializer(ModelSerializer):
    marginal_distribution = JSONField()
    conditional_distribution = JSONField()

    class Meta:
        model = Slice
        fields = ('from_value', 'to_value', 'marginal_distribution', 'conditional_distribution')
