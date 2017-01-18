from rest_framework.serializers import ModelSerializer, JSONField, PrimaryKeyRelatedField
from features.models import Sample, Feature, Bin, Slice, Session, Dataset, RarResult


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'mean', 'variance', 'min', 'max',)


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
        fields = ('from_value', 'deviation', 'frequency', 'significance', 'to_value',
                  'marginal_distribution', 'conditional_distribution')


class DatasetSerializer(ModelSerializer):
    class Meta:
        model = Dataset
        fields = ('id', 'name')


class SessionSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=True) # TODO: Make writable
    dataset = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Dataset.objects.all())

    class Meta:
        model = Session
        fields = ('id', 'dataset', 'target')


class RarResultSerializer(ModelSerializer):
    feature = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = RarResult
        fields = ('id', 'feature', 'relevancy', 'redundancy', 'rank')
