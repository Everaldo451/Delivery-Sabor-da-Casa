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

### Docker

Na pasta `backend`, copie `.env.example` para `.env` e configure `JWT_SECRET_KEY`
e `POSTGRES_PASSWORD`. O Compose de producao inicia PostgreSQL, MongoDB, Redis e
a API; os bancos usam volumes nomeados para preservar os dados:

As imagens de producao e de teste usam `latest` para PostgreSQL e Redis; o Mongo
usa `latest` em producao e `mongo:4.4.29` nos testes. A API e construida pelo
Compose diretamente do Dockerfile apropriado para cada ambiente.

```powershell
docker compose --env-file .env -f docker/docker-compose.yaml up -d --build
docker compose --env-file .env -f docker/docker-compose.yaml exec app /app/.venv/bin/alembic upgrade head
```

O Compose de teste instala as dependencias de desenvolvimento e inclui `tests/`.
Os dados dos bancos ficam em armazenamento temporario e desaparecem quando os
containers sao removidos:

```powershell
docker compose --env-file .env -f docker/docker-compose.test.yaml up --build --abort-on-container-exit --exit-code-from app
docker compose --env-file .env -f docker/docker-compose.test.yaml down
```

Os dois Compose devem ser executados a partir de `backend`. O container da API
usa os nomes dos servicos como hosts dos bancos; a porta `8000` e publicada no
host e as portas dos bancos permanecem apenas na rede interna do Compose.

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

Cardapio: categorias e pratos ficam no PostgreSQL. As categorias iniciais
`Pratos`, `Bebidas` e `Sobremesas` sao criadas pela migration. As rotas de
consulta sao `GET /cardapio/categorias`, `GET /cardapio?categoria=Pratos`
(filtro opcional) e `GET /cardapio/{prato_id}`. Criacao, edicao e remocao de
pratos e categorias exigem usuario administrador: `POST /cardapio/categorias`,
`PUT` e `DELETE /cardapio/categorias/{categoria_id}`. Uma categoria com pratos
vinculados nao pode ser removida. Imagens enviadas por
`PUT /cardapio/{prato_id}/imagem` sao armazenadas em binario no PostgreSQL
(JPEG, PNG ou WebP, ate 5 MiB); `GET` no mesmo caminho serve a imagem e `DELETE`
remove-a. O upload recebe os bytes diretamente no corpo e o `Content-Type` deve
informar o formato. A resposta do prato inclui `imagem: {url, content_type}`;
os bytes e o tipo MIME ficam no PostgreSQL.
