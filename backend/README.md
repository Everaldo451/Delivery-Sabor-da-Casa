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

### Seed local do PostgreSQL

Com o PostgreSQL ativo e as migrations aplicadas, configure
`SEED_ADMIN_PASSWORD` e `SEED_USER_PASSWORD` no `backend/.env` e execute:

```powershell
python -m uv run python -m seed.postgres.seed
```

O seed cria/atualiza um administrador (`admin@delivery.local`), um cliente
(`cliente@delivery.local`), quatro categorias e 40 pratos de demonstração. Os
Compose definem `admin12345` e `usuario12345` como senhas padrão do seed; no
Compose de produção, configure senhas próprias no `.env` antes de executá-lo.
Os registros estão em `seed/postgres/*.json`; as senhas nunca ficam nos arquivos
de dados e são gravadas no PostgreSQL com hash bcrypt. A execução é idempotente.
Uma imagem padrão opcional pode ser colocada em
`seed/postgres/assets/prato-padrao.png`; sem esse arquivo, os pratos são criados
sem imagem.

### Seed local do MongoDB

Com o MongoDB ativo, execute da pasta `backend` para importar ou atualizar as
sete zonas de entrega do arquivo `seed/mongodb/zonas_jp.json`:

```powershell
python -m uv run python -m seed.mongodb.seed
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

Ele possui valores padrao para `POSTGRES_PASSWORD`, `JWT_SECRET_KEY`,
`SEED_ADMIN_PASSWORD` (`admin12345`) e `SEED_USER_PASSWORD` (`usuario12345`),
entao nao precisa definir essas variaveis no arquivo .env. Em ambientes persistentes, defina
senhas proprias para os usuarios do seed antes de executa-lo.

```powershell
docker compose -f docker/docker-compose.test.yaml up --build --abort-on-container-exit --exit-code-from app
docker compose -f docker/docker-compose.test.yaml down
```

Os testes estao separados por responsabilidade em `tests/routers`,
`tests/repositories` e `tests/services`. Os testes HTTP usam um `TestClient` com
servicos substituidos por mocks; o `conftest.py` de repositories aplica as
migrations do Alembic quando `RUN_REPOSITORY_MIGRATIONS=1`, definido no Compose
de teste.
Os testes de repositories usam clientes/sessoes controlados para verificar as
conversoes e chamadas aos bancos sem depender de dados persistentes.

Os dois Compose devem ser executados a partir de `backend`. O container da API
usa os nomes dos servicos como hosts dos bancos; a porta `8000` e publicada no
host e as portas dos bancos permanecem apenas na rede interna do Compose.

Autenticacao: `POST /auth/login` recebe `email` e `senha` e retorna um access
token (30 minutos) e um refresh token (7 dias). Envie o access token no header
`Authorization: Bearer <access_token>`. Quando ele expirar, envie
`POST /auth/refresh` com `{"refresh_token": "<refresh_token>"}` para receber um
novo par de tokens; o refresh token anterior e revogado durante a rotacao.
Para encerrar a sessao, chame `POST /auth/logout` com o access token no header e
o refresh token no corpo: `{"refresh_token": "<refresh_token>"}`. O refresh
token e opcional para compatibilidade, mas sem ele somente o access token atual
e revogado.

Carrinho: as rotas autenticadas em `/carrinho` guardam os itens no Redis, na chave
`carrinho:<user_id>`. `GET /carrinho` consulta (e retorna vazio se ainda nao existir),
`PUT /carrinho` substitui os itens, `POST /carrinho/itens` adiciona quantidades,
`PATCH /carrinho/itens/{prato_id}` altera quantidade e observacao,
`DELETE /carrinho/itens/{prato_id}` remove um item e `DELETE /carrinho` limpa o
carrinho. O carrinho expira apos um dia sem atualizacoes. Ele armazena o
identificador do prato, quantidade e observacao; precos e disponibilidade
continuam sendo validados ao criar o pedido.

Ao criar um pedido, informe um CEP brasileiro com 8 digitos, com ou sem hifen.
O backend consulta o ViaCEP e rejeita CEPs nao encontrados antes de persistir
o pedido. Se o ViaCEP estiver indisponivel, a criacao retorna erro temporario
e pode ser tentada novamente.

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

Favoritos: usuário autenticado pode listar seus favoritos com `GET /favoritos`,
adicionar com `PUT /favoritos/{prato_id}` e remover com
`DELETE /favoritos/{prato_id}`. A relação usuário-prato é armazenada no
PostgreSQL; adicionar o mesmo prato novamente não duplica o registro.

Cupons: administradores criam, editam e removem cupons em `/cupons`; a listagem
`GET /cupons` exibe os cupons ativos e dentro da validade, e `GET /cupons/admin`
lista todos os cupons para administração. Usuário autenticado
pode validar um código com `POST /cupons/validar`, enviando código e subtotal.
Cupons suportam desconto percentual ou valor fixo, subtotal mínimo, período de
validade e limite máximo para desconto percentual. No pedido, envie
`cupom_codigo`; o backend calcula o desconto sobre os itens e impede que ele
ultrapasse o subtotal. `limite_usos` define o total de resgates e `limite_por_usuario` limita o uso por cliente (1 por padrão). `somente_novos_clientes` restringe o cupom a quem ainda não tem pagamento aprovado. O uso é reservado ao criar o pedido e liberado se ele for cancelado.

Fidelidade: `GET /fidelidade` consulta o saldo e
`GET /fidelidade/transacoes` consulta o extrato. Cada R$ 1,00 em pagamento
aprovado acumula 1 ponto; 100 pontos valem R$ 1,00 de desconto. Para resgatar,
envie `pontos_resgatados` ao criar o pedido. O saldo é debitado atomicamente;
os pontos resgatados são devolvidos se o pedido for cancelado. O extrato SQL
torna os créditos de pedidos idempotentes.
