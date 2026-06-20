import json
from functools import wraps

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.authtoken.models import Token

from .models import Chat, Message


# ---------------------------------------------------------------------------
# Paginas (templates)
# ---------------------------------------------------------------------------

def LoginPageView(Request):
    """
    Serve a pagina de login/registro. A sessao real e controlada via
    token no localStorage (JS), nao via sessao do Django, entao essa
    view nao faz nenhuma checagem de autenticacao no backend.
    """
    return render(Request, "login.html")


def ChatPageView(Request):
    """
    Serve a pagina principal do chat. O JS verifica se ha um token
    salvo no localStorage e redireciona para /login/ caso nao haja.
    """
    return render(Request, "chat.html")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ParseJsonBody(Request):
    """
    Le o corpo da requisicao como JSON. Retorna um dict vazio se o body
    estiver vazio ou nao for um JSON valido (mantem a logica simples,
    sem levantar exception pro caller tratar).
    """
    try:
        return json.loads(Request.body or "{}")
    except json.JSONDecodeError:
        return {}


def GetUserFromToken(Request):
    """
    Extrai e valida o token enviado no header Authorization no formato:
    "Authorization: Token <chave>". Retorna o User correspondente ou
    None se o token for invalido/ausente.
    """
    AuthHeader = Request.headers.get("Authorization", "")
    Parts = AuthHeader.split()
    if len(Parts) != 2 or Parts[0] != "Token":
        return None

    TokenKey = Parts[1]
    try:
        TokenObject = Token.objects.select_related("user").get(key=TokenKey)
    except Token.DoesNotExist:
        return None

    return TokenObject.user


def LoginRequired(ViewFunction):
    """
    Decorator que exige um token valido no header Authorization.
    Se valido, injeta o usuario autenticado como Request.AuthUser.
    """

    @wraps(ViewFunction)
    def Wrapper(Request, *Args, **Kwargs):
        AuthUser = GetUserFromToken(Request)
        if AuthUser is None:
            return JsonResponse(
                {"error": "Token de autenticacao invalido ou ausente."},
                status=401,
            )
        Request.AuthUser = AuthUser
        return ViewFunction(Request, *Args, **Kwargs)

    return Wrapper


def SerializeUser(UserObject):
    return {
        "id": UserObject.id,
        "username": UserObject.username,
    }


def SerializeMessage(MessageObject):
    return {
        "id": MessageObject.id,
        "chatId": MessageObject.Chat_id,
        "senderId": MessageObject.Sender_id,
        "senderUsername": MessageObject.Sender.username,
        "content": MessageObject.Content,
        "createdAt": MessageObject.CreatedAt.isoformat(),
    }


def SerializeChat(ChatObject):
    return {
        "id": ChatObject.id,
        "name": ChatObject.Name,
        "isGroup": ChatObject.IsGroup,
        "participants": [
            SerializeUser(Participant)
            for Participant in ChatObject.Participants.all()
        ],
        "createdAt": ChatObject.CreatedAt.isoformat(),
    }


# ---------------------------------------------------------------------------
# Autenticacao / Usuario
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
def RegisterView(Request):
    """
    Cria um novo usuario. Espera JSON: { "username": ..., "password": ... }
    """
    Body = ParseJsonBody(Request)
    Username = Body.get("username", "").strip()
    Password = Body.get("password", "")

    if not Username or not Password:
        return JsonResponse(
            {"error": "Campos 'username' e 'password' sao obrigatorios."},
            status=400,
        )

    if User.objects.filter(username=Username).exists():
        return JsonResponse(
            {"error": "Esse nome de usuario ja esta em uso."},
            status=409,
        )

    NewUser = User.objects.create_user(username=Username, password=Password)
    NewToken = Token.objects.create(user=NewUser)

    return JsonResponse(
        {
            "user": SerializeUser(NewUser),
            "token": NewToken.key,
        },
        status=201,
    )


@csrf_exempt
@require_http_methods(["POST"])
def LoginView(Request):
    """
    Autentica um usuario existente. Espera JSON:
    { "username": ..., "password": ... }
    Retorna o token a ser usado no header Authorization das demais rotas.
    """
    Body = ParseJsonBody(Request)
    Username = Body.get("username", "").strip()
    Password = Body.get("password", "")

    AuthenticatedUser = authenticate(
        Request, username=Username, password=Password
    )
    if AuthenticatedUser is None:
        return JsonResponse(
            {"error": "Usuario ou senha invalidos."},
            status=401,
        )

    UserToken, _ = Token.objects.get_or_create(user=AuthenticatedUser)

    return JsonResponse(
        {
            "user": SerializeUser(AuthenticatedUser),
            "token": UserToken.key,
        },
        status=200,
    )


# ---------------------------------------------------------------------------
# Chats / Mensagens
# ---------------------------------------------------------------------------

@csrf_exempt
@require_http_methods(["POST"])
@LoginRequired
def CreateChatView(Request):
    """
    Cria um chat novo entre o usuario autenticado e um ou mais
    destinatarios, cobrindo tanto 1:1 quanto 1:N.

    Espera JSON: { "recipientIds": [2, 3, ...], "name": "opcional" }
    Se "recipientIds" tiver 1 elemento -> chat 1:1.
    Se tiver mais de 1 -> chat em grupo (1:N).
    """
    Body = ParseJsonBody(Request)
    RecipientIds = Body.get("recipientIds", [])
    Name = Body.get("name")

    if not isinstance(RecipientIds, list) or not RecipientIds:
        return JsonResponse(
            {"error": "Informe 'recipientIds' com ao menos um destinatario."},
            status=400,
        )

    Recipients = User.objects.filter(id__in=RecipientIds)
    if Recipients.count() != len(set(RecipientIds)):
        return JsonResponse(
            {"error": "Um ou mais 'recipientIds' nao foram encontrados."},
            status=404,
        )

    IsGroup = len(RecipientIds) > 1

    NewChat = Chat.objects.create(
        IsGroup=IsGroup,
        Name=Name,
        CreatedBy=Request.AuthUser,
    )
    NewChat.Participants.add(Request.AuthUser, *Recipients)

    return JsonResponse(SerializeChat(NewChat), status=201)


@csrf_exempt
@require_http_methods(["GET"])
@LoginRequired
def ListChatsView(Request):
    """
    Lista todos os chats em que o usuario autenticado participa.
    """
    UserChats = Chat.objects.filter(Participants=Request.AuthUser).order_by(
        "-CreatedAt"
    )
    return JsonResponse(
        {"chats": [SerializeChat(ChatItem) for ChatItem in UserChats]},
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
@LoginRequired
def SendMessageView(Request, ChatId):
    """
    Envia uma mensagem para um chat existente (1:1 ou 1:N, a logica e
    a mesma: a mensagem fica associada ao Chat e visivel a todos os
    Participants).

    Espera JSON: { "content": "texto da mensagem" }
    """
    try:
        TargetChat = Chat.objects.get(id=ChatId, Participants=Request.AuthUser)
    except Chat.DoesNotExist:
        return JsonResponse(
            {"error": "Chat nao encontrado ou usuario nao participa dele."},
            status=404,
        )

    Body = ParseJsonBody(Request)
    Content = Body.get("content", "").strip()
    if not Content:
        return JsonResponse(
            {"error": "Campo 'content' e obrigatorio."},
            status=400,
        )

    NewMessage = Message.objects.create(
        Chat=TargetChat,
        Sender=Request.AuthUser,
        Content=Content,
    )

    return JsonResponse(SerializeMessage(NewMessage), status=201)


@csrf_exempt
@require_http_methods(["GET"])
@LoginRequired
def MessageHistoryView(Request, ChatId):
    """
    Retorna o historico de mensagens de um chat especifico, em ordem
    cronologica. Apenas participantes do chat podem ver o historico.
    """
    try:
        TargetChat = Chat.objects.get(id=ChatId, Participants=Request.AuthUser)
    except Chat.DoesNotExist:
        return JsonResponse(
            {"error": "Chat nao encontrado ou usuario nao participa dele."},
            status=404,
        )

    ChatMessages = TargetChat.Messages.select_related("Sender").all()

    return JsonResponse(
        {
            "chatId": TargetChat.id,
            "messages": [
                SerializeMessage(MessageItem) for MessageItem in ChatMessages
            ],
        },
        status=200,
    )