import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import Admin.routing  # import your websocket routes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SchoolProject.settings')

# This is your default Django HTTP app
django_asgi_app = get_asgi_application()

# Channels ASGI application to handle HTTP and WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            Admin.routing.websocket_urlpatterns
        )
    ),
})
