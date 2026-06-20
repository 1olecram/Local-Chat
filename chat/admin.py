from django.contrib import admin

from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "Name", "IsGroup", "CreatedBy", "CreatedAt")
    filter_horizontal = ("Participants",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "Chat", "Sender", "Content", "CreatedAt")
