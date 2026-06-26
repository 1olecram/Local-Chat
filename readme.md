# Local Chat

Sistema de chat distribuído desenvolvido para a disciplina de Sistemas Distribuídos — CEFET-MG, 2026/1.

O sistema possui suporte a mensagens em tempo real (WebSockets) via Django Channels e Daphne, autenticação por token, criação de chats privados (1:1) e em grupo (1:N), e interface web responsiva (mobile-first) com suporte a acesso simplificado via celular por QR Code.

---

## Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:

- Python 3.10 ou superior
- Docker e Docker Compose
- Git
- Ngrok (opcional, para testes em rede externa/dispositivos móveis)

---

## Guia de Instalação e Execução Completa

Siga os passos abaixo para clonar, configurar e executar a aplicação localmente:

### 1. Clonar o Repositório

```bash
git clone https://github.com/1olecram/Local-Chat.git
cd Local-Chat
```

### 2. Configurar o Ambiente Virtual (venv)

No Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Iniciar o Banco de Dados (PostgreSQL via Docker)

O projeto utiliza um container PostgreSQL para persistência. Inicie o container em segundo plano:

```bash
docker compose up -d
```

> **Nota:** O banco é iniciado na porta externa `5435` para evitar conflito caso você já possua um serviço PostgreSQL local rodando na porta padrão `5432`.
> As credenciais padrão configuradas no container são:
>
> - **Banco:** `local_chat`
> - **Usuário:** `postgres`
> - **Senha:** `916810`
> - **Porta Externa:** `5435`
> - **Porta Interna:** `5432`

### 5. Aplicar as Migrations do Django

Crie as tabelas necessárias no banco de dados executando as migrações:

```bash
DB_PORT=5435 python manage.py migrate
```

### 6. Criar um Superusuário (Opcional)

Permite acessar o painel de administração do Django para inspecionar e gerenciar registros de usuários, chats e mensagens:

```bash
DB_PORT=5435 python manage.py createsuperuser
```

### 7. Iniciar o Servidor

Como o projeto utiliza comunicação bidirecional em tempo real via WebSockets, é altamente recomendado iniciar o servidor ASGI **Daphne**:

```bash
DB_PORT=5435 daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

Ou utilizando o comando tradicional do Django (que foi configurado para utilizar Daphne como servidor de desenvolvimento):

```bash
DB_PORT=5435 python manage.py runserver
```

### 8. Acessar a Aplicação

- **Interface de Chat:** [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/)
- **Painel Administrativo:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## Integração com Ngrok (Testes no Celular)

O projeto possui um mecanismo dinâmico para facilitar testes em dispositivos móveis. A página de login gera um QR Code com base no endereço usado para acessá-la. Expor o servidor local com o **ngrok** permite testar o comportamento responsivo e o chat em tempo real diretamente do celular:

1. Certifique-se de que o servidor Django esteja rodando localmente na porta `8000`.
2. Em um novo terminal, execute o ngrok para expor a porta local à internet:
   ```bash
   ngrok http 8000
   ```
3. O ngrok gerará uma URL pública segura, como `https://a1b2-c3d4-e5f6.ngrok-free.app`.
4. Acesse essa URL pública no navegador do seu computador.
5. No rodapé da tela de login, na seção **"Acesse pelo celular"**, o sistema renderizará um QR Code com a URL do ngrok.
6. Escaneie o QR Code com a câmera do seu celular. O site será aberto no aparelho.
7. Com a configuração `ALLOWED_HOSTS = ['*']` em `core/settings.py`, o Django aceitará as conexões vindas do domínio do ngrok sem gerar erros de host bloqueado, permitindo o fluxo de login e a troca de mensagens via WebSockets.

---

## Gerenciamento do Banco de Dados com Docker

### 1. Comandos Básicos do Container

- **Subir o banco de dados:** `docker compose up -d`
- **Verificar se o container está rodando:** `docker ps`
- **Visualizar os logs do banco:** `docker compose logs db`
- **Parar o banco de dados:** `docker compose down`

### 2. Acessando o Banco via Terminal

Para conectar diretamente ao terminal do PostgreSQL dentro do container rodando, execute o comando:

```bash
docker exec -it local_chat_db psql -U postgres -d local_chat
```

### 3. Exibindo os Dados de Mensagens Completas (Consulta SQL)

Como o Django mapeia os campos definidos em CamelCase/PascalCase na model (por exemplo, `Content`, `Sender`, `Chat`, `CreatedAt`), as tabelas correspondentes no PostgreSQL possuem nomes de colunas case-sensitive. Portanto, **essas colunas devem ser escritas com aspas duplas** nas consultas manuais.

Para visualizar o histórico completo de mensagens com os respectivos remetentes, execute a seguinte consulta dentro do terminal do `psql`:

```sql
SELECT 
    m.id AS mensagem_id,
    m."Chat_id" AS chat_id,
    u.username AS remetente,
    m."Content" AS conteudo,
    m."CreatedAt" AS data_envio
FROM 
    chat_message m
JOIN 
    auth_user u ON m."Sender_id" = u.id
ORDER BY 
    m."CreatedAt" ASC;
```

#### Exemplo de Retorno no Terminal:

```
 mensagem_id | chat_id | remetente |  conteudo  |          data_envio     
-------------+---------+-----------+------------+-------------------------------
           1 |       1 | marcelo   | oi         | 2026-06-25 01:06:24.876359+00
           2 |       1 | admin     | Oi         | 2026-06-25 01:06:46.428853+00
           3 |       1 | marcelo   | Como está? | 2026-06-25 01:19:28.678676+00
           4 |       1 | admin     | bem e vc ? | 2026-06-25 01:20:04.794467+00
           5 |       1 | marcelo   | Melhor agr | 2026-06-25 01:20:12.674979+00
           6 |       3 | admin     | oi         | 2026-06-25 01:22:41.299569+00
           7 |       3 | teste     | Oi pessoal | 2026-06-25 01:23:05.67371+00
           8 |       3 | marcelo   | Oi!        | 2026-06-25 01:23:13.080616+00
           9 |       4 | teste     | Oi carlos  | 2026-06-25 01:45:55.835595+00
          10 |       4 | carlos    | oi         | 2026-06-25 01:54:00.813577+00
(10 rows)
```

Para encerrar a sessão do terminal do PostgreSQL, digite:

```sql
\q
```

---

## Estrutura do Projeto

```
Local-Chat/
├── chat/                  # Microsserviço de mensagens/chat
│   ├── models.py          # Modelos Chat e Message
│   ├── views.py           # Rotas de auth, chats e mensagens + páginas
│   ├── urls.py            # Rotas da API (/api/...)
│   └── migrations/
├── core/                  # Configuração do projeto Django
│   ├── settings.py        # Configuração de banco, apps instalados
│   ├── urls.py            # Rotas raiz (/admin/, /api/, /login/, /chat/)
│   └── asgi.py            # Configuração ASGI (Channels/Daphne)
├── templates/
│   ├── base.html          # Layout base
│   ├── login.html         # Tela de login/registro
│   └── chat.html          # Tela principal do chat
└── requirements.txt
```

---

## Rotas da API

Todas as rotas abaixo (exceto registro/login) exigem o cabeçalho `Authorization: Token <token>` no request, obtido no login ou registro.

| Método | Rota                               | Descrição                                             |
| ------- | ---------------------------------- | ------------------------------------------------------- |
| POST    | `/api/auth/register/`            | Cria um novo usuário                                   |
| POST    | `/api/auth/login/`               | Autentica e retorna o token                             |
| GET     | `/api/users/`                    | Lista todos os usuários cadastrados, exceto o próprio |
| GET     | `/api/users/search/?q=`          | Busca usuários pelo nome (contém o texto informado)   |
| GET     | `/api/chats/`                    | Lista os chats do usuário autenticado                  |
| POST    | `/api/chats/create/`             | Cria um chat (1:1 ou em grupo)                          |
| GET     | `/api/chats/<id>/messages/`      | Histórico de mensagens de um chat                      |
| POST    | `/api/chats/<id>/messages/send/` | Envia uma mensagem em um chat                           |

---
