from rest_framework.serializers import ModelSerializer, JSONField
from features.models import Sample, Feature, Bin, Slice, Target


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('name', 'relevancy', 'redundancy', 'rank', 'mean', 'variance',
                  'min', 'max')


class TargetSerializer(ModelSerializer):
    feature = FeatureSerializer(many=False)

    class Meta:
        model = Target
        fields = ('feature', )


class BinSerializer(ModelSerializer):
    class Meta:
        model = Bin
        fields = ('from_value', 'to_value', 'count')


class SampleSerializer(ModelSerializer):
    class Meta:
        model = Sample
        fields = ('value',)


class SliceSerializer(ModelSerializer):
    marginal_distribution = JSONField()
    conditional_distribution = JSONField()

    class Meta:
        model = Slice
        fields = ('from_value', 'deviation', 'frequency', 'significance', 'to_value', 'marginal_distribution', 'conditional_distribution')
