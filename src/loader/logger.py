# from utils import secrets
from loguru import logger
from notifiers.logging import NotificationHandler
import os


if os.getenv("IS_PROD") == 'True':
    handler = NotificationHandler(
        "slack", defaults=dict(webhook_url=os.getenv("SLACK_WEBHOOK")),
    )
    
    logger.add(handler, level="ERROR", diagnose=True)
