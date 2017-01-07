from channels.routing import route_class
from features.channels import EventConsumer

channel_routing = [
    route_class(EventConsumer, path='^/socket')
]
