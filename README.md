# Delivery-Sabor-da-Casa

## Backend

Copie `backend/.env.example` para `backend/.env` e configure `JWT_SECRET_KEY`
com uma chave aleatoria de pelo menos 32 bytes. Gere uma com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

O login usa usuários previamente provisionados na tabela `users`; não há
endpoint público de cadastro. O campo `senha_hash` deve conter um hash bcrypt.
O Redis local deve estar ativo; ele armazena os tokens revogados até a expiração.

Instale as dependências com uv:

```powershell
cd backend
python -m uv sync --group dev
python -m uv run uvicorn app.main:app --reload
```

Autenticacao: `POST /auth/login` recebe `email` e `senha`; envie o JWT retornado
no header `Authorization: Bearer <token>`. `POST /auth/logout` revoga esse token.