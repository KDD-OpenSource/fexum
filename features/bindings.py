from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, RarResult
from users.models import User


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['dataset-{0}-updates'.format(instance.id)]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False


class RarResultBinding(WebsocketBinding):
    model = RarResult
    stream = 'rar_result'
    fields = ['id', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['rar-result-{0}-updates'.format(instance.id)]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False

