# Plataforma de Avaliação de Funcionários

Aplicação web desenvolvida como desafio técnico para explorar uma hierarquia organizacional e
registrar avaliações semanais de desempenho entre líderes e seus subordinados.

## Sobre o projeto

A plataforma permite escolher um líder ativo, visualizar seus subordinados diretos e indiretos,
enviar avaliações por meio de seis perguntas ponderadas e consultar a avaliação principal de cada
funcionário. A interface está disponível nos modos claro e escuro.

## Funcionalidades

- seleção e persistência do líder ativo;
- visualização da hierarquia direta e indireta;
- avaliações semanais com seis perguntas e notas de 1 a 4;
- avaliações imutáveis após o envio;
- consulta da avaliação principal, incluindo autor, respostas e pesos históricos;
- tratamento de autorização, duplicidade semanal e estados vazios;
- tema claro ou escuro com preferência persistida.

## Tecnologias

- **Frontend:** React 18, TypeScript 5 e Vite 6;
- **Backend:** Python 3.10+, FastAPI, SQLAlchemy e Alembic;
- **Banco de dados:** PostgreSQL 16;
- **Testes:** Pytest com PostgreSQL real;
- **Ambiente:** Docker e Docker Compose.

## Arquitetura

O backend separa responsabilidades no fluxo `API → Service → Repository → PostgreSQL`. A camada de
API trata contratos HTTP, os serviços concentram regras de negócio e os repositórios executam a
persistência e as consultas recursivas específicas do PostgreSQL.

O frontend organiza componentes, páginas, hooks, serviços HTTP e tipos TypeScript. As chamadas
protegidas passam por um cliente centralizado que adiciona `X-Leader-Id`.

O detalhamento das decisões está no [Design Técnico](./docs/technical-design.md).

## Estrutura do projeto

```text
backend/          API, serviços, persistência, migrações, seed e testes
frontend/         aplicação React e configuração do Vite
docs/             design técnico, histórias e diagramas
compose.yaml      ambiente completo de desenvolvimento
.env.example      variáveis utilizadas pelo Docker Compose
README.md         instruções de execução e uso
```

## Pré-requisitos

### Fluxo recomendado

- Docker 24 ou superior;
- Docker Compose 2 ou superior.

### Execução manual

- Python 3.10 ou superior;
- Node.js 22 e npm;
- PostgreSQL 16, ou os bancos PostgreSQL iniciados pelo Compose.

## Configuração

Na raiz do projeto, crie o arquivo utilizado pelo Compose:

```bash
cp .env.example .env
```

Os valores padrão usam portas que evitam a instalação PostgreSQL comum da porta `5432`:

| Serviço | Porta padrão no host |
|---|---:|
| PostgreSQL de desenvolvimento | `5434` |
| PostgreSQL de testes | `5433` |
| Backend | `8000` |
| Frontend | `5173` |

As portas podem ser alteradas no `.env`. Dentro da rede Docker, os dois bancos continuam ouvindo
na porta `5432`.

As credenciais presentes no exemplo são exclusivas para demonstração local. Não devem ser usadas
em produção.

## Executando com Docker

Construa e inicie o ambiente completo:

```bash
docker compose up --build -d
docker compose ps
```

O ambiente contém quatro serviços:

- `postgres`: banco persistente de desenvolvimento;
- `postgres-test`: banco isolado utilizado somente pelos testes;
- `backend`: API FastAPI;
- `frontend`: servidor de desenvolvimento Vite.

Ao iniciar, o backend aguarda os bancos, aplica `alembic upgrade head` e executa o seed idempotente.
O seed não apaga avaliações existentes nem reinicializa o banco.

Para acompanhar a inicialização:

```bash
docker compose logs -f backend frontend
```

As migrações e o seed também podem ser executados explicitamente:

```bash
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m scripts.seed
```

Para encerrar os containers preservando os dados:

```bash
docker compose down
```

Para remover todos os volumes do ambiente e começar novamente, use
`docker compose down --volumes`. Esse comando apaga o banco de desenvolvimento e também os volumes
descartáveis de dependências, build e cache mantidos pelo Compose.

## Executando sem Docker

### Bancos PostgreSQL

É possível usar somente os bancos do Compose:

```bash
cp .env.example .env
docker compose up -d postgres postgres-test
```

### Backend

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python -m scripts.seed
python -m uvicorn app.main:app --reload
```

O arquivo [backend/.env.example](./backend/.env.example) aponta para os bancos nas portas `5434` e
`5433` do host.

### Frontend

Em outro terminal:

```bash
cd frontend
npm ci
npm run dev
```

Por padrão, o Vite encaminha chamadas relativas a `/api` para `http://127.0.0.1:8000`. A variável
`VITE_API_PROXY_TARGET` altera esse destino e é configurada automaticamente no Compose.

## Banco de dados

As migrações ficam em `backend/alembic/versions` e devem ser executadas a partir de `backend/`:

```bash
python -m alembic upgrade head
```

O seed é executado com:

```bash
python -m scripts.seed
```

Ele cria a fixture original do desafio:

- 20 funcionários;
- 19 relações da hierarquia organizacional;
- 6 perguntas fixas de avaliação.

O seed é idempotente quando a fixture já está correta. Caso encontre funcionários, relações ou
perguntas divergentes, ele interrompe a execução em vez de sobrescrever dados silenciosamente.

O banco de testes é separado do banco de desenvolvimento. A suíte exige que
`TEST_DATABASE_URL` aponte para um banco cujo nome termine em `_test`; antes da sessão de testes,
as migrações e a fixture são recriadas nesse banco.

## Testes

Com Docker:

```bash
docker compose exec backend python -W error -m pytest
docker compose exec frontend npx tsc -b --pretty false
docker compose exec frontend npm run build
```

Sem Docker, com o ambiente virtual ativo:

```bash
cd backend
python -W error -m pytest

cd ../frontend
npx tsc -b --pretty false
npm run build
```

O frontend ainda não possui uma suíte automatizada própria; a validação disponível é a compilação
TypeScript e o build de produção.

## Uso da aplicação

1. Acesse `http://localhost:5173`.
2. Selecione o líder que representará a identidade ativa.
3. Consulte os subordinados diretos e indiretos em **Minha equipe**.
4. Use **Avaliar** para responder às seis perguntas e enviar uma avaliação.
5. Use **Ver avaliação** para consultar a avaliação principal do funcionário.
6. Use o controle de tema para alternar entre os modos claro e escuro.

O identificador do líder é armazenado no `localStorage` com a chave `actingLeaderId`. Requisições
protegidas enviam esse valor no cabeçalho `X-Leader-Id`.

Esse mecanismo é apenas uma identidade simplificada para o desafio técnico. Ele **não é uma
autenticação segura** e não substitui login, sessão ou controle de acesso de produção.

A preferência de tema é armazenada separadamente na chave `theme`. Alterar o tema não modifica o
líder ativo.

## Regras de negócio

- um líder pode avaliar subordinados diretos e indiretos;
- cada combinação líder, funcionário e semana permite uma única avaliação;
- líderes diferentes podem avaliar o mesmo funcionário na mesma semana;
- cada avaliação responde às seis perguntas fixas com notas inteiras de 1 a 4;
- a nota final é calculada no backend a partir dos pesos `25, 20, 20, 15, 10, 10`;
- avaliações enviadas são imutáveis;
- a avaliação principal usa primeiro a semana mais recente;
- dentro da mesma semana, vence o avaliador de maior posição na hierarquia global;
- persistindo o empate, vence a avaliação enviada mais recentemente.

Uma avaliação de semana nova sempre tem prioridade sobre uma avaliação antiga, independentemente
da posição de seu autor.

## API

A API fica disponível em `http://localhost:8000`. A documentação Swagger/OpenAPI está em
`http://localhost:8000/docs`.

Rotas públicas:

- `GET /health`;
- `GET /api/leaders`;
- `GET /api/evaluation/questions`.

Rotas protegidas principais:

- `GET /api/me/subordinates`;
- `POST /api/evaluations`;
- `GET /api/employees/{employee_id}/evaluations/latest`.

As rotas protegidas exigem `X-Leader-Id` com o identificador de um funcionário existente. O backend
continua responsável por verificar se o funcionário-alvo pertence à subárvore dessa identidade.

## Documentação

- [Design Técnico](./docs/technical-design.md)
- [Histórias de Usuário e Critérios de Aceitação](./docs/user-stories.md)

## Decisões de escopo

- não há login, senha, JWT ou OAuth;
- não há edição ou exclusão de avaliações;
- não há histórico opcional de avaliações;
- as perguntas são fixas conforme o desafio;
- a arquitetura foi mantida proporcional à escala do desafio técnico.
