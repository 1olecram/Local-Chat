from django.conf import settings
from django.db import models


class Chat(models.Model):
    """
    Representa uma conversa. Pode ser 1:1 (2 participantes) ou 1:N
    (varios participantes / grupo). Nao ha diferenca estrutural entre
    os dois casos, apenas a quantidade de Participants.
    """

    Participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="Chats",
    )
    IsGroup = models.BooleanField(default=False)
    Name = models.CharField(max_length=120, blank=True, null=True)
    CreatedBy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="CreatedChats",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    CreatedAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.Name:
            return self.Name
        return f"Chat#{self.pk}"


class Message(models.Model):
    """
    Mensagem individual dentro de um Chat. Historico fica todo aqui,
    persistido no banco para ser recuperado depois.
    """

    Chat = models.ForeignKey(
        Chat,
        related_name="Messages",
        on_delete=models.CASCADE,
    )
    Sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="SentMessages",
        on_delete=models.CASCADE,
    )
    Content = models.TextField()
    CreatedAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["CreatedAt"]

    def __str__(self):
        return f"{self.Sender}: {self.Content[:30]}"
