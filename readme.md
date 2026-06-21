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

### 2. Criar o banco de dados

Crie um banco chamado `local_chat` no seu PostgreSQL (via pgAdmin, ou
pelo `psql`):

```sql
CREATE DATABASE local_chat;
```

### 3. ⚠️ Configurar a senha do banco (passo obrigatório)

O arquivo `core/settings.py` lê a configuração do banco a partir de
variáveis de ambiente, com valores padrão de fallback:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'local_chat'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

**Se a senha do seu usuário `postgres` local não for `postgres`**, o
projeto não vai conseguir conectar no banco. Você tem duas opções:

- **Opção A (mais simples):** edite diretamente o valor padrão no
  `core/settings.py`, trocando `'postgres'` em `DB_PASSWORD` pela sua
  senha real.
- **Opção B:** defina a variável de ambiente antes de rodar os
  comandos, sem precisar editar o código:
  ```powershell
  $env:DB_PASSWORD = "sua_senha_aqui"
  ```

> Isso vale também para `DB_USER`, `DB_NAME`, `DB_HOST` e `DB_PORT`,
> caso seu ambiente use valores diferentes dos padrões.

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
python manage.py migrate
```

Se der erro de conexão aqui, volte ao passo 3 — geralmente é a senha
do banco.

### 7. (Opcional) Criar um superusuário

Permite acessar o painel administrativo em `/admin/` para inspecionar
usuários, chats e mensagens direto pelo navegador.

```bash
python manage.py createsuperuser
```

### 8. Rodar o servidor

```bash
python manage.py runserver
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
- A interface de chat atualiza mensagens por polling (a cada 3s), não
  via WebSocket — a integração com Channels/Daphne (já presente nas
  dependências do projeto) é um próximo passo pendente.
- A criação de conversas usa busca por nome de usuário e uma listagem
  geral de usuários cadastrados, em vez de exigir o ID do destinatário
  — mais próximo da experiência de apps de chat reais.

## Pendências conhecidas

- Comunicação em tempo real via WebSocket ainda não implementada
  (atualmente é feita por polling no front-end).
- Testes automatizados (unitários, integração, carga) ainda não
  cobrem os novos endpoints.