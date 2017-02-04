from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, RelevancyResult, RedundancyResult


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['dataset-updates']

    def has_permission(self, user, action, pk):
        return True


class RelevancyResultBinding(WebsocketBinding):
    model = RelevancyResult
    stream = 'relevancy_result'
    fields = ['id']

    @classmethod
    def group_names(cls, instance):
        return ['relevancy-result-updates']

    def has_permission(self, user, action, pk):
        return True


class RedundancyResultBinding(WebsocketBinding):
    model = RedundancyResult
    stream = 'redundancy_result'
    fields = ['id']

    @classmethod
    def group_names(cls, instance):
        return ['redundancy-result-updates']

    def has_permission(self, user, action, pk):
        return True
