from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView
from django.conf import settings

from chat import views as chat_views

urlpatterns = [
    path('', RedirectView.as_view(url='/chat/')),
    path('admin/', admin.site.urls),
    path('api/', include('chat.urls')),
    path('login/', chat_views.LoginPageView, name='login-page'),
    path('chat/', chat_views.ChatPageView, name='chat-page'),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'favicon.ico')),
]