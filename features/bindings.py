from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, RarResult


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['dataset-updates']

    def has_permission(self, user, action, pk):
        return True


class RarResultBinding(WebsocketBinding):
    model = RarResult
    stream = 'rar_result'
    fields = ['id', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['rar-result-updates']

    def has_permission(self, user, action, pk):
        return True

