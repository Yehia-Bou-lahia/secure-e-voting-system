"""
ASGI config for encryption_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from voting.consumers import VotingConsumer   # We'll create this later

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'encryption_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/vote/", VotingConsumer.as_asgi()),
        ])
    ),
})