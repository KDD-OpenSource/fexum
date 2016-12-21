from rest_framework.serializers import ModelSerializer, JSONField
from features.models import Feature, Bin, Histogram, Slice


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'relevancy', 'redundancy', 'rank', 'is_target', 'mean', 'variance',
                  'min', 'max')


class BinSerializer(ModelSerializer):
    class Meta:
        model = Bin
        fields = ('from_value', 'to_value', 'count')


class HistogramSerializer(ModelSerializer):
    bin_set = BinSerializer(read_only=True, many=True)

    class Meta:
        model = Histogram
        fields = ('id', 'bin_set')


class SliceSerializer(ModelSerializer):
    marginal_distribution = JSONField()
    conditional_distribution = JSONField()

    class Meta:
        model = Slice
        fields = ('from_value', 'to_value', 'marginal_distribution', 'conditional_distribution')
