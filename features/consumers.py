from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding, RarResultBinding
from users.models import User


class Demultiplexer(WebsocketDemultiplexer):
    consumers = {
        'dataset': DatasetBinding.consumer,
        'rar_result': RarResultBinding.consumer
    }

    def connection_groups(self):
        users = User.objects.all()
        dataset_groups = ['user-{0}-dataset-updates' for user in users]
        rar_result_groups = ['user-{0}-rar-result-updates' for user in users]
        return dataset_groups + rar_result_groups
