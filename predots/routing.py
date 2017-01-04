from channels.routing import route
from features.consumers import ws_connect, ws_message, ws_disconnect

channel_routing = [
    route('websocket.connect', ws_connect, path=r"^/socket"),
    route('websocket.receive', ws_message, path=r"^/socket"),
    route('websocket.disconnect', ws_disconnect, path=r"^/socket"),
]
