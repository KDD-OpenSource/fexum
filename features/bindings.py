from channels.binding.websockets import WebsocketBinding
from rest_framework.serializers import ModelSerializer
from features.models import Feature


class RelevancyBinding(WebsocketBinding):
    model = Feature
    stream = 'relevancy'
    fields = ['name', 'relevancy']

    @classmethod
    def group_names(cls, *args, **kwargs):
        return ['binding.values']

    def has_permission(self, user, action, pk):
        return True
