# Local Chat

Sistema de chat distribuído desenvolvido para a disciplina de Sistemas
Distribuídos — CEFET-MG, 2026/1.

Backend em Django, com autenticação por token e troca de mensagens 1:1 e
1:N, persistidas em PostgreSQL.

## Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL instalado e em execução
- Git

## Passo a passo para rodar localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/1olecram/Local-Chat.git
cd Local-Chat
```

### 2. Iniciar o Banco de Dados (PostgreSQL via Docker)

O projeto está configurado para utilizar PostgreSQL. Para subir uma instância local rapidamente com Docker Compose:

```bash
docker compose up -d
```

> **Nota:** O banco será iniciado no host na porta `5435` para evitar conflitos caso você já possua um PostgreSQL local rodando na porta padrão `5432`.
> As credenciais padrão do banco configuradas no container são:
> - **Banco:** `local_chat`
> - **Usuário:** `postgres`
> - **Senha:** `916810`
> - **Porta:** `5435`


### 4. Criar e ativar o ambiente virtual

```powershell
python -m venv venv
venv\Scripts\activate
```

No Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 5. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 6. Aplicar as migrations

```bash
DB_PORT=5435 python manage.py migrate
```

### 7. (Opcional) Criar um superusuário

Permite acessar o painel administrativo em `/admin/` para inspecionar usuários, chats e mensagens.

```bash
DB_PORT=5435 python manage.py createsuperuser
```

### 8. Rodar o servidor ASGI (Daphne)

Como o projeto utiliza comunicação em tempo real via WebSockets, é recomendado iniciar o servidor ASGI **Daphne**:

```bash
DB_PORT=5435 daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

Ou usando o comando de desenvolvimento do Django (que foi configurado para usar Daphne):

```bash
DB_PORT=5435 python manage.py runserver
```

### 9. Acessar a aplicação

- Interface de chat: [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- Painel administrativo: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

## Estrutura do projeto

```
Local-Chat/
├── chat/                  # Microsserviço de mensagens/chat
│   ├── models.py          # Modelos Chat e Message
│   ├── views.py           # Rotas de auth, chats e mensagens + páginas
│   ├── urls.py            # Rotas da API (/api/...)
│   └── migrations/
├── core/                  # Configuração do projeto Django
│   ├── settings.py        # Configuração de banco, apps instalados
│   ├── urls.py             # Rotas raiz (/admin/, /api/, /login/, /chat/)
│   └── asgi.py             # Configuração ASGI (Channels/Daphne)
├── templates/
│   ├── base.html           # Layout base
│   ├── login.html          # Tela de login/registro
│   └── chat.html            # Tela principal do chat
└── requirements.txt
```

## Rotas da API

Todas as rotas abaixo (exceto registro/login) exigem o header
`Authorization: Token <token>`, obtido no login ou registro.

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/register/` | Cria um novo usuário |
| POST | `/api/auth/login/` | Autentica e retorna o token |
| GET | `/api/users/` | Lista todos os usuários cadastrados, exceto o próprio |
| GET | `/api/users/search/?q=` | Busca usuários pelo nome (contém o texto informado) |
| GET | `/api/chats/` | Lista os chats do usuário autenticado |
| POST | `/api/chats/create/` | Cria um chat (1:1 ou em grupo) |
| GET | `/api/chats/<id>/messages/` | Histórico de mensagens de um chat |
| POST | `/api/chats/<id>/messages/send/` | Envia uma mensagem em um chat |

## Decisões de projeto

- Autenticação usa o `User` padrão do `django.contrib.auth`, com
  token simples via `rest_framework.authtoken` (sem usar DRF nas
  rotas em si — são views function-based puras do Django).
- Um único modelo `Chat` cobre tanto conversas 1:1 quanto em grupo
  (1:N): a diferença é apenas a quantidade de `Participants`.
- A interface de chat e a comunicação em tempo real foram completamente implementadas com WebSockets utilizando Django Channels e Daphne, removendo a necessidade de polling síncrono.
- A criação de conversas usa busca por nome de usuário e uma listagem
  geral de usuários cadastrados, em vez de exigir o ID do destinatário
  — mais próximo da experiência de apps de chat reais.

## Pendências conhecidas

- Testes automatizados (unitários, integração, carga) ainda não
  cobrem os novos endpoints.