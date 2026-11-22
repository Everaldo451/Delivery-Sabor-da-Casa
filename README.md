# Delivery-Sabor-da-Casa

## Backend

Copie `backend/.env.example` para `backend/.env` e configure `JWT_SECRET_KEY`
com uma chave aleatoria de pelo menos 32 bytes. Gere uma com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

O cadastro público está disponível em `POST /users`, com `nome`, `email` e
`senha`. As senhas são armazenadas com hash bcrypt. O Redis local deve estar
ativo; ele armazena os tokens revogados até a expiração.

Instale as dependências com uv:

```powershell
cd backend
python -m uv sync --group dev
python -m uv run alembic upgrade head
python -m uv run uvicorn app.main:app --reload
```

As alterações do schema PostgreSQL são versionadas com Alembic. Para um banco
existente criado pelo app antes da adoção do Alembic, marque a revisão-base e
aplique as migrations pendentes:

```powershell
python -m uv run alembic stamp 20261121_01
python -m uv run alembic upgrade head
```

Essa adoção pressupõe que as tabelas `users` e `payments` já existam. A migration
interrompe a atualização se encontrar pagamentos sem usuário correspondente,
para que esses dados sejam corrigidos antes de criar a foreign key.

Para gerar uma migration a partir de alterações nos modelos:

```powershell
python -m uv run alembic revision --autogenerate -m "descricao da alteracao"
```

Revise sempre o arquivo gerado antes de aplicar `alembic upgrade head`.

Autenticacao: `POST /auth/login` recebe `email` e `senha`; envie o JWT retornado
no header `Authorization: Bearer <token>`. `POST /auth/logout` revoga esse token.

Carrinho: as rotas autenticadas em `/carrinho` guardam os itens no Redis, na chave
`carrinho:<user_id>`. `GET /carrinho` consulta (e retorna vazio se ainda nao existir),
`PUT /carrinho` substitui os itens, `POST /carrinho/itens` adiciona quantidades,
`PATCH /carrinho/itens/{prato_id}` altera quantidade e observacao,
`DELETE /carrinho/itens/{prato_id}` remove um item e `DELETE /carrinho` limpa o
carrinho. O carrinho expira apos um dia sem atualizacoes. Ele armazena o
identificador do prato, quantidade e observacao; precos e disponibilidade
continuam sendo validados ao criar o pedido.
