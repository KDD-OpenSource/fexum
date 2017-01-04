from channels import Group

GROUP_NAME = 'features'


def ws_connect(message):
    Group(GROUP_NAME).add(message.reply_channel)


def ws_message(message):
    pass


def ws_disconnect(message):
    Group(GROUP_NAME).discard(message.reply_channel)
