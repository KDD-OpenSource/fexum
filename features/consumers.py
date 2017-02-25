from channels.generic.websockets import WebsocketDemultiplexer
from features.bindings import DatasetBinding, RarResultBinding
from features.models import RarResult, Experiment


class Demultiplexer(WebsocketDemultiplexer):
    http_user = True

    consumers = {
        'dataset': DatasetBinding.consumer,
        'rar_result': RarResultBinding.consumer
    }

    def connection_groups(self, **kwargs):
        user = self.message.user

        if user.is_anonymous:
            return []

        experiments = Experiment.objects.filter(user=user).all()
        dataset_groups = ['dataset-{0}-updates'.format(experiment.dataset.id) for experiment in
                          experiments]

        rar_results = RarResult.objects.filter(target__experiment__in=experiments)
        rar_result_groups = ['rar-result-{0}-updates'.format(rar_result.id) for rar_result in
                             rar_results]

        return dataset_groups + rar_result_groups
