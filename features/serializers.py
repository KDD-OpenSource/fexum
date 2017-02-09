from rest_framework.serializers import ModelSerializer, JSONField, PrimaryKeyRelatedField, \
    SerializerMethodField, Serializer, FloatField, ModelField
from features.models import Sample, Feature, Bin, Slice, Experiment, Dataset, Redundancy, \
    Relevancy
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
        fields = ('value', 'order')


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
            'feature': obj.relevancy.feature.id,
            'from_value': obj.from_value,
            'to_value': obj.to_value
        }]


class DatasetSerializer(ModelSerializer):
    class Meta:
        model = Dataset
        fields = ('id', 'name', 'status')


class ExperimentSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=True)
    dataset = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Dataset.objects.all())

    class Meta:
        model = Experiment
        fields = ('id', 'dataset', 'target')


class ExperimentTargetSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Feature.objects.all())

    class Meta:
        model = Experiment
        fields = ('target',)

    def validate(self, data):
        # TODO: Test
        if data.get('target').dataset != self.instance.dataset:
            raise ValidationError({'target': 'Target must be from the same dataset.'})
        return data


class RelevancySerializer(ModelSerializer):
    feature = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Relevancy
        fields = ('id', 'feature', 'relevancy', 'rank')


class RedundancySerializer(ModelSerializer):
    first_feature = PrimaryKeyRelatedField(many=False, read_only=True)
    second_feature = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Redundancy
        fields = ('id', 'first_feature', 'second_feature', 'redundancy', 'weight')


class ConditionalDistributionRequestSerializer(Serializer):
    feature = PrimaryKeyRelatedField(queryset=Feature.objects.all())
    from_value = FloatField(required=True)
    to_value = FloatField(required=True)


class ConditionalDistributionResultSerializer(Serializer):
    value = FloatField(required=True)
    probability = FloatField(required=True)
