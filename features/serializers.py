from rest_framework.serializers import ModelSerializer, JSONField
from features.models import Sample, Feature, Bin, Histogram, Slice, Target


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'relevancy', 'redundancy', 'rank', 'mean', 'variance',
                  'min', 'max')


class TargetSerializer(ModelSerializer):
    feature = FeatureSerializer(read_only=True, many=False)

    class Meta:
        model = Target
        fields = ('feature', )


class BinSerializer(ModelSerializer):
    class Meta:
        model = Bin
        fields = ('from_value', 'to_value', 'count')


class HistogramSerializer(ModelSerializer):
    bin_set = BinSerializer(read_only=True, many=True)

    class Meta:
        model = Histogram
        fields = ('id', 'bin_set')


class SampleSerializer(ModelSerializer):
    class Meta:
        model = Sample
        fields = ('value',)


class SliceSerializer(ModelSerializer):
    marginal_distribution = JSONField()
    conditional_distribution = JSONField()

    class Meta:
        model = Slice
        fields = ('from_value', 'to_value', 'marginal_distribution', 'conditional_distribution')
