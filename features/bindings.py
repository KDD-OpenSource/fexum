from channels.binding.websockets import WebsocketBinding
from features.models import RelevancyResult, RedundancyResult


class RelevancyResultBinding(WebsocketBinding):
    model = RelevancyResult
    stream = 'relevancy_result'
    fields = ['feature', 'relevancy', 'rank']

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ['relevancy_result-updates']

    def has_permission(self, user, action, pk):
        return True


class RedundancyResultBinding(WebsocketBinding):
    model = RedundancyResult
    stream = 'redundancy_result'
    fields = ['first_feature', 'second_feature', 'redundancy']

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ['redundancy_result-updates']

    def has_permission(self, user, action, pk):
        return True
