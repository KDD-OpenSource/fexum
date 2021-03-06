from rest_framework.serializers import ModelSerializer, JSONField, PrimaryKeyRelatedField, \
    SerializerMethodField, Serializer, ListField, FloatField, IntegerField
from rest_framework.validators import ValidationError

from features.models import Feature, Bin, Slice, Experiment, Dataset, Redundancy, \
    Relevancy, Spectrogram, Calculation


class FeatureSerializer(ModelSerializer):
    class Meta:
        model = Feature
        fields = ('id', 'name', 'mean', 'variance', 'min', 'max', 'is_categorical', 'categories')

    categories = JSONField()


class BinSerializer(ModelSerializer):
    class Meta:
        model = Bin
        fields = ('from_value', 'to_value', 'count')


class FeatureSliceSerializer(ModelSerializer):
    features = SerializerMethodField()

    class Meta:
        model = Slice
        fields = ('features', 'deviation', 'frequency')

    def get_features(self, obj):
        # TODO: Optimized cache?
        return [{
            'feature': obj.relevancy.feature.id,
            'range': {
                'from_value': obj.from_value,
                'to_value': obj.to_value
            },
            'categories': None  # TODO: Implement, algorithm does not return categories right now
        }]


class DatasetSerializer(ModelSerializer):
    class Meta:
        model = Dataset
        fields = ('id', 'name', 'status')


class ExperimentSerializer(ModelSerializer):
    target = PrimaryKeyRelatedField(many=False, read_only=True)
    dataset = PrimaryKeyRelatedField(many=False, read_only=False, queryset=Dataset.objects.all())
    analysis_selection = PrimaryKeyRelatedField(many=True, read_only=False, queryset=Feature.objects.all())
    visibility_blacklist = PrimaryKeyRelatedField(many=True, read_only=False, queryset=Feature.objects.all())

    class Meta:
        model = Experiment
        fields = ('id', 'dataset', 'target', 'visibility_text_filter', 'visibility_rank_filter', 'analysis_selection',
                  'visibility_blacklist', 'visibility_exclude_filter')

    def validate(self, data):

        if self.instance is not None and self.instance.target is not None and data.get(
                'dataset') is not None and self.instance.target.dataset != data.get('dataset'):
            raise ValidationError('Dataset cannot be changed if target is set.')

        dataset = data.get('dataset') or self.instance.dataset

        for feature in data.get('analysis_selection', []):
            if feature.dataset != dataset:
                raise ValidationError('All selected features have to be part of the experiment\'s dataset')

        for feature in data.get('visibility_blacklist', []):
            if feature.dataset != dataset:
                raise ValidationError('All blacklisted features have to be part of the experiment\'s dataset')

        return data


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
    features = PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Relevancy
        fields = ('id', 'features', 'relevancy', 'iteration')


class RedundancySerializer(ModelSerializer):
    first_feature = PrimaryKeyRelatedField(many=False, read_only=True)
    second_feature = PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Redundancy
        fields = ('id', 'first_feature', 'second_feature', 'redundancy', 'weight')


class RangeSerializer(Serializer):
    from_value = FloatField(required=True)
    to_value = FloatField(required=True)

    def validate(self, attrs):
        if attrs['from_value'] > attrs['to_value']:
            raise ValidationError('from_value has to be smaller than to_value')
        return attrs


class ConditionalDistributionRequestSerializer(Serializer):
    feature = PrimaryKeyRelatedField(queryset=Feature.objects.all())
    range = RangeSerializer(required=False)
    categories = ListField(required=False)

    def validate(self, attrs):
        if (attrs.get('categories') is None) == (attrs.get('range') is None):
            raise ValidationError('Specify either a range or categories.')
        return attrs


class DensitySerializer(Serializer):
    target_class = FloatField(required=True)
    density_values = ListField(required=True)


class SpectrogramSerializer(ModelSerializer):
    image_url = SerializerMethodField()

    class Meta:
        model = Spectrogram
        fields = ('width', 'height', 'image_url')

    def get_image_url(self, obj):
        # FIXME: Use obj.image.url instead of hardcoded path
        return '/media/spectrograms/{0}.png'.format(obj.feature.id)


class CalculationSerializer(ModelSerializer):
    target = SerializerMethodField()
    features = SerializerMethodField()

    class Meta:
        model = Calculation
        fields = ('id', 'max_iteration', 'current_iteration', 'type', 'target', 'features')

    def get_target(self, obj: Calculation):
        return obj.result_calculation_map.target.id

    def get_features(self, obj: Calculation):
        if obj.type != Calculation.FIXED_FEATURE_SET_HICS:
            return None

        return [feature.id for feature in obj.features.all()]
