from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, Experiment


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        return ['dataset-{0}-updates'.format(instance)]

    def has_permission(self, user, action, pk):
        """
        The user should not be able to change dataset using channels
        """
        return False


class TargetBinding(WebsocketBinding):
    pass # TODO
