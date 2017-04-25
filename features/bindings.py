from channels.binding.websockets import WebsocketBinding
from features.models import Dataset, Calculation, Experiment


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance):
        experiments = Experiment.objects.filter(dataset=instance)
        user_by_experiment_groups = ['user-{0}-updates'.format(experiment.user_id) for experiment in experiments]
        uploader_group = ['user-{0}-updates'.format(instance.uploaded_by_id)]
        return user_by_experiment_groups + uploader_group

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False


class CalculationBinding(WebsocketBinding):
    model = Calculation
    stream = 'calculation'
    fields = ['id', 'status', 'type']

    @classmethod
    def group_names(cls, instance):
        experiments = Experiment.objects.filter(target=instance.result_calculation_map.target)
        return ['user-{0}-updates'.format(experiment.user_id) for experiment in experiments]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False
