from rest_framework.serializers import ModelSerializer, JSONField, PrimaryKeyRelatedField, \
    SerializerMethodField
from features.models import Sample, Feature, Bin, Slice, Session, Dataset, RedundancyResult, \
    RelevancyResult
from rest_framework.validators import ValidationError


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'mean', 'variance', 'min', 'max', 'is_categorical')


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
        fields = ('from_value', 'deviation', 'frequency', 'to_value',
                  'marginal_distribution', 'conditional_distribution')


class FeatureSliceSerializer(ModelSerializer):
    features = SerializerMethodField()

    class Meta:
        model = Slice
        fields = ('features', 'deviation', 'frequency')

    def get_features(self, obj):
        # TODO: Optimized cache?
        return [{
            'feature': obj.relevancy_result.feature.id,
            'from_value': obj.from_value,
            'to_value': obj.to_value
        }]


class DatasetSerializer(ModelSerializer):
    class Meta:
        model = Dataset
        fields = ('id', 'name')


class SessionSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=True)
    dataset = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Dataset.objects.all())

    class Meta:
        model = Session
        fields = ('id', 'dataset', 'target')


class SessionTargetSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Feature.objects.all())

    class Meta:
        model = Session
        fields = ('target',)

    def validate(self, data):
        if data.get('target').dataset != self.instance.dataset:
            raise ValidationError({'target': 'Target must be from the same dataset.'})
        return data


class RelevancyResultSerializer(ModelSerializer):
    feature = PrimaryKeyRelatedField(many=False, read_only=True)
    target = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = RelevancyResult
        fields = ('id', 'feature', 'relevancy', 'rank', 'target')


class RedundancyResultSerializer(ModelSerializer):
    first_feature = PrimaryKeyRelatedField(many=False, read_only=True)
    second_feature = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = RedundancyResult
        fields = ('id', 'first_feature', 'second_feature', 'redundancy')
