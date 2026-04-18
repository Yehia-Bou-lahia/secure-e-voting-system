from django.urls import path
from .consumers import VotingConsumer

websocket_urlpatterns = [
    path('ws/vote', VotingConsumer.as_asgi()),
]
