# Projeto MIRAI

Plataforma de monitoramento de poluição luminosa e ofuscamento viário no Brasil.
Projeto Integrador — Análise e Desenvolvimento de Sistemas.

---

## Stack

| Camada   | Tecnologia              |
|----------|-------------------------|
| Frontend | HTML + CSS + JavaScript |
| Mapa     | Leaflet.js + NASA GIBS  |
| Backend  | Python · Flask          |
| Banco    | SQLite                  |
| Auth     | JWT (JSON Web Token)    |

---

## Estrutura

```
mirai/
├── app.py              # Servidor Flask + API
├── database.py         # (integrado em app.py neste projeto)
├── schema.sql          # Estrutura do banco
├── requirements.txt    # Dependências Python
├── mirai.db            # Banco SQLite (criado automaticamente)
├── README.md
│
├── index.html          # Landing page
├── login.html          # Tela de login
├── register.html       # Tela de cadastro
└── mirai.html          # Dashboard (mapa)
```

---

## Como rodar

### 1. Pré-requisitos
- Python 3.10 ou superior
- pip

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Iniciar o servidor

```bash
python app.py
```

Saída esperada no terminal:
```
✓ Banco de dados pronto: mirai.db
╔════════════════════════════════════════════════╗
║   PROJETO MIRAI - Backend em execução          ║
║   http://localhost:5000                        ║
╚════════════════════════════════════════════════╝
```

### 4. Acessar no navegador

Abra **http://localhost:5000**

---

## Rotas da API

Todas as respostas são em JSON.

| Método | Rota               | Auth | Descrição                       |
|--------|--------------------|------|---------------------------------|
| POST   | `/api/register`    | —    | Cadastro de novo usuário        |
| POST   | `/api/login`       | —    | Login, retorna token JWT        |
| GET    | `/api/me`          | ✅   | Dados do usuário logado         |
| POST   | `/api/logout`      | —    | Logout (simbólico)              |
| GET    | `/api/indicadores` | ✅   | Indicadores do dashboard        |

### Exemplo — cadastro

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"João", "email":"joao@email.com", "password":"123456"}'
```

### Exemplo — login

```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com", "password":"123456"}'
```

Resposta:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { "id": 1, "email": "joao@email.com", "name": "João" }
}
```

### Exemplo — rota protegida

```bash
curl http://localhost:5000/api/me \
  -H "Authorization: Bearer <token_recebido_no_login>"
```

---

## Fluxo de autenticação

1. Usuário preenche formulário em `/register` ou `/login`
2. Frontend envia `POST /api/register` ou `/api/login`
3. Backend valida e retorna um **token JWT**
4. Frontend guarda o token no `localStorage`
5. Em requisições futuras, o token é enviado no header:
   `Authorization: Bearer <token>`
6. Backend valida o token antes de liberar rotas protegidas

---

## Banco de dados

O arquivo `mirai.db` é criado automaticamente na primeira execução.

### Tabela `users`

| Coluna         | Tipo       | Observação                 |
|----------------|------------|----------------------------|
| id             | INTEGER PK | AUTOINCREMENT              |
| email          | TEXT UQ    | Único                      |
| password_hash  | TEXT       | Hash Werkzeug (pbkdf2)     |
| name           | TEXT       | Nome do usuário            |
| created_at     | TIMESTAMP  | Data do cadastro           |
| last_login     | TIMESTAMP  | Último login               |

### Tabela `measurements` (preparada para próxima etapa)

Armazenará medições SQM coletadas por usuários no mapa.

---

## Próximos passos

- [ ] Proteger o acesso ao dashboard (`/mirai`) validando o token no cliente
- [ ] Adicionar botão de logout no dashboard
- [ ] Endpoint pra salvar medições que o usuário criar no mapa
- [ ] Exibir nome do usuário logado no header do dashboard
- [ ] Recuperação de senha
- [ ] Perfil do usuário

---

## Observações técnicas

- **Senha**: nunca é armazenada em texto puro, apenas o hash gerado por `werkzeug.security.generate_password_hash` (pbkdf2 com sha256).
- **Token JWT**: expira em 7 dias (configurável em `app.py`).
- **SECRET_KEY**: o valor atual (`mirai-dev-secret-change-in-prod`) é apenas para desenvolvimento. Em produção, deve ser carregado de variável de ambiente.
- **CORS**: não é necessário porque o Flask serve o frontend e a API na mesma origem.
