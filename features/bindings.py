from channels.binding.websockets import WebsocketBinding
from features.models import RarResult


class RarResultBinding(WebsocketBinding):
    model = RarResult
    stream = 'rar_result'
    fields = ['feature', 'relevancy', 'redundancy', 'rank']

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ['rar_result-updates']

    def has_permission(self, user, action, pk):
        return True
