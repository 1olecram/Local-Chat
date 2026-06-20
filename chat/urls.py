from django.urls import path

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView, name="register"),
    path("auth/login/", views.LoginView, name="login"),
    path("chats/", views.ListChatsView, name="list-chats"),
    path("chats/create/", views.CreateChatView, name="create-chat"),
    path("chats/<int:ChatId>/messages/", views.MessageHistoryView, name="message-history"),
    path("chats/<int:ChatId>/messages/send/", views.SendMessageView, name="send-message"),
]
