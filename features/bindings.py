from typing import List

from channels.binding.websockets import WebsocketBinding

from features.models import Dataset, Calculation, CurrentExperiment
from features.serializers import CalculationSerializer


class DatasetBinding(WebsocketBinding):
    model = Dataset
    stream = 'dataset'
    fields = ['name', 'status']

    @classmethod
    def group_names(cls, instance: Dataset) -> List[str]:
        current_experiments = CurrentExperiment.objects.filter(experiment__dataset=instance)
        user_by_current_experiment_groups = ['user-{0}-updates'.format(current_experiment.experiment.user_id) for
                                             current_experiment in
                                             current_experiments]
        uploader_group = ['user-{0}-updates'.format(instance.uploaded_by_id)]
        return user_by_current_experiment_groups + uploader_group

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False


class CalculationBinding(WebsocketBinding):
    model = Calculation
    stream = 'calculation'
    fields = CalculationSerializer.fields

    @classmethod
    def group_names(cls, instance: Calculation):
        current_experiments = CurrentExperiment.objects.filter(
            experiment__target=instance.result_calculation_map.target)
        return ['user-{0}-updates'.format(current_experiment.experiment.user_id) for current_experiment in
                current_experiments]

    def has_permission(self, user, action, pk):
        # Permission is always false to block inbound messages that change the model
        return False

    def serialize_data(self, instance: Calculation):
        return CalculationSerializer(instance=instance).data
