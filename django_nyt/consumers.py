import logging

from . import models, settings

logger = logging.getLogger(__name__)

try:
    channels_ver = "1"
    from channels import Group
    from channels.auth import channel_session_user, channel_session_user_from_http
except Exception as e:
    logger.info("Not using channels 1. Attempting channels 2...")
    channels_ver = "2"
    from channels.generic.websocket import AsyncJsonWebsocketConsumer
    from channels.layers import get_channel_layer
    from channels.db import database_sync_to_async
    from asgiref.sync import async_to_sync

    # create channels v1 decorators so that imports don't break
    def channel_session_user(func):
        def wrapper():
            raise Exception("[django-nyt:consumers] Channels 2 detected: {} function should not be called".format(func))
        return wrapper
    
    def channel_session_user_from_http(func):
        def wrapper():
            raise Exception("[django-nyt:consumers]Channels 2 detected: {} function should not be called".format(func))
        return wrapper

"""
Channels version 1 consumer functions
"""
def get_subscriptions(message):
    """
    :return: Subscription query for a given message's user
    """
    if message.user.is_authenticated:
        return models.Subscription.objects.filter(settings__user=message.user)
    else:
        return models.Subscription.objects.none()

@channel_session_user_from_http
def ws_connect(message):
    """
    Connected to websocket.connect
    """
    logger.debug("Adding new connection for user {}".format(message.user))
    message.reply_channel.send({"accept": True})

    for subscription in get_subscriptions(message):
        Group(
            settings.NOTIFICATION_CHANNEL.format(
                notification_key=subscription.notification_type.key
            )
        ).add(message.reply_channel)


@channel_session_user
def ws_disconnect(message):
    """
    Connected to websocket.disconnect
    """
    logger.debug("Removing connection for user {} (disconnect)".format(message.user))
    for subscription in get_subscriptions(message):
        Group(
            settings.NOTIFICATION_CHANNEL.format(
                notification_key=subscription.notification_type.key
            )
        ).discard(message.reply_channel)


def ws_receive(message):
    """
    Receives messages, this is currently just for debugging purposes as there
    is no communication API for the websockets.
    """
    logger.debug("Received a message, responding with a non-API message")
    message.reply_channel.send({'text': 'OK'})

"""
Channels version 2 consumer class
"""
class NYTconsumer(AsyncJsonWebsocketConsumer):
     
    async def connect(self):
        """
        Connected to websocket
        """
        logger.debug("Adding new connection for user {}".format(self.scope["user"]))

        await self.channel_layer.group_add(
            settings.NOTIFICATION_CHANNEL.format(
                notification_key=subscriptions.notification_type.key
            ),
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self):
        """
        Websocket closed
        """

        await self.channel_layer.group_discard(
            settings.NOTIFICATION_CHANNEL.format(
                notification_key=subscriptions.notification_type.key
            ),
            self.channel_name
        )

    async def receive_json(self, content):
        """
        Received a message. Do nothing.
        """
        pass

    async def notification(self, event):
        """
        Sending notification text
        """

        await self.send_json({
            'text': event.get('text', None),
        })

    #async def get_subscriptions(self):
    #    """
    #    :return: Subscription query for a given message's user
    #    """
    #    if self.scope["user"].is_authenticated:
    #        subcriptions = await database_sync_to_async(models.Subscription.objects.filter(settings__user=self.scope["user"]))()
    #    else:
    #        subcriptions = await database_sync_to_async(models.Subscription.objects.none())()
    #    return subscriptions
