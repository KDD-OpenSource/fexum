from channels import Group


def ws_connect(message):
    Group("chat").add(message.reply_channel)


def ws_message(message):
    Group("chat").send({
        "text": "[user] %s" % message.content['text'],
    })


def ws_disconnect(message):
    Group("chat").discard(message.reply_channel)
