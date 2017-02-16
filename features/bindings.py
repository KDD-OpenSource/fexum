from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, RarResult
from users.models import User


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        users = User.objects.filter(experiment__dataset=instance)
        return ['user-{0}-dataset-updates'.format(user.id) for user in users]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False


class RarResultBinding(WebsocketBinding):
    model = RarResult
    stream = 'rar_result'
    fields = ['id', 'status']

    @classmethod
    def group_names(cls, instance):
        users = User.objects.filter(experiment__target=instance.target)
        return ['user-{0}-rar-result-updates'.format(user.id) for user in users]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False

