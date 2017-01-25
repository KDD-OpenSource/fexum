from channels.binding.websockets import WebsocketBinding
from features.models import RelevancyResult


class RelevancyResultBinding(WebsocketBinding):
    model = RelevancyResult
    stream = 'relevancy_result'
    fields = ['feature', 'relevancy', 'rank']

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ['relevancy_result-updates']

    def has_permission(self, user, action, pk):
        return True
