import logging

try:
    channels_ver = "1"
    from channels import Group
except Exception as e:
    logger.info("Not using channels 1. Attempting channels 2...")
    channels_ver = "2"
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

from . import models, settings

logger = logging.getLogger(__name__)

def notify_via_channels_v1(notification_type):
    g = Group(
        settings.NOTIFICATION_CHANNEL.format(
            notification_key=notification_type['key']
        )
    )
    g.send(
        {'text': 'new-notification'}
    )

def notify_via_channels_v2(notification_type):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        settings.NOTIFICATION_CHANNEL.format(
            notification_key=notification_type['key']
        ),
        {
            'type': 'notification',
            'text': 'new-notification',
        },
    )

def notify_subscribers(notifications, key):
    """
    Notify all open channels about new notifications
    """

    logger.debug("Broadcasting to subscribers")

    notification_type_ids = models.NotificationType.objects.values('key').filter(key=key)

    for notification_type in notification_type_ids:
        
        if channels_ver == "1":
            notify_via_channels_v1(notification_type)
        elif channels_ver == "2":
            notify_via_channels_v2(notification_type)
        else:
            raise Exception("[django-nyt:subscribers] Unknown channels version")
