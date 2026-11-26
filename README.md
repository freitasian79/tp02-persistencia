# Sistema de Gestão de Eventos

API REST para gerenciamento de eventos, locais, palestrantes, participantes, atividades, inscrições e controle de presença, desenvolvida para o Trabalho Prático 2 da disciplina **QXD0099 - Desenvolvimento de Software para Persistência** (UFC - Campus Quixadá).

## Integrantes
* André Souza
* Ian Freitas
* Jeová Alison

## Tema e Objetivo
* **Tema 5:** Sistema de Gestão de Eventos.
* **Objetivo:** Disponibilizar uma API REST com persistência relacional (PostgreSQL e SQLite) que gerencie a programação de eventos acadêmicos/técnicos, relacionamentos entre entidades, consultas filtradas, estatísticas agregadas e controle de vagas das atividades.

## Tecnologias Utilizadas
* **Python 3**
* **FastAPI** (rotas organizadas em `APIRouter`)
* **SQLAlchemy 2.0** (ORM, relacionamentos, constraints e consultas agregadas)
* **Alembic** (controle e evolução de migrações de esquema)
* **Pydantic / Pydantic Settings** (validação de entrada/saída e leitura de `.env`)
* **PostgreSQL 16** (via `psycopg` e Docker Compose) e **SQLite**
* **Uvicorn** (servidor ASGI)

---

## Modelo de Dados

### Entidades Principais
1. **Evento (`eventos`):** evento principal com nome único, tipo (`congresso`, `seminario`, `simposio`, `workshop`, `outro`), período (`data_inicio` <= `data_fim`), organizador e status (`ativo`, `cancelado`, `encerrado`).
2. **Local (`locais`):** espaço físico (`auditorio`, `sala`, `laboratorio`, `outro`) com capacidade positiva, localização, recursos e flag `ativo`.
3. **Palestrante (`palestrantes`):** ministrante com nome, e-mail único, área de atuação e mini-bio.
4. **Participante (`participantes`):** usuário com nome, e-mail e CPF únicos (11 dígitos), telefone, instituição e flag `ativo`.
5. **Atividade (`atividades`):** palestra, oficina, minicurso ou mesa-redonda vinculada a um `Evento` e a um `Local`, com horário (`fim > inicio`), `capacidade`, `carga_horaria` e `status`.
6. **Inscrição (`inscricoes`):** associação entre `Participante` e `Atividade` com status (`pendente`, `confirmada`, `cancelada`), data e observação, impedindo duplicidade por par `(participante_id, atividade_id)`.
7. **Presença (`presencas`):** registro de check-in (`manual` ou `qrcode`) vinculado de forma exclusiva a uma `Inscricao`.

### Relacionamentos
* **1:1 — `Inscricao` ↔ `Presenca`:** cada inscrição confirmada pode gerar no máximo um registro de presença (`unique=True` em `presencas.inscricao_id`).
* **1:N — `Evento` → `Atividade` e `Local` → `Atividade`:** um evento possui várias atividades e um local recebe várias atividades em horários distintos.
* **N:N — `Atividade` ↔ `Palestrante`:** implementado pela tabela associativa `atividade_palestrante`.
* **N:N com atributos — `Participante` ↔ `Atividade`:** modelado via entidade associativa `Inscricao`.

### Representação do Modelo Relacional

```mermaid
erDiagram
    EVENTOS ||--o{ ATIVIDADES : "possui (1:N)"
    LOCAIS ||--o{ ATIVIDADES : "recebe (1:N)"
    ATIVIDADES }o--o{ PALESTRANTES : "atividade_palestrante (N:N)"
    PARTICIPANTES ||--o{ INSCRICOES : "realiza (1:N)"
    ATIVIDADES ||--o{ INSCRICOES : "recebe (1:N)"
    INSCRICOES ||--o| PRESENCAS : "gera check-in (1:1)"

    EVENTOS {
        int id PK
        string nome UK
        string tipo
        date data_inicio
        date data_fim
        string status
    }
    LOCAIS {
        int id PK
        string nome UK
        string tipo
        int capacidade
        bool ativo
    }
    ATIVIDADES {
        int id PK
        int evento_id FK
        int local_id FK
        string titulo
        datetime inicio
        datetime fim
        int capacidade
        int carga_horaria
        string status
    }
    PALESTRANTES {
        int id PK
        string nome
        string email UK
        string area_atuacao
    }
    PARTICIPANTES {
        int id PK
        string nome
        string email UK
        string cpf UK
        bool ativo
    }
    INSCRICOES {
        int id PK
        int participante_id FK
        int atividade_id FK
        string status
        datetime data_inscricao
    }
    PRESENCAS {
        int id PK
        int inscricao_id FK,UK
        datetime registrada_em
        string metodo
    }
```

---

## Instalação e Execução

### 1. Ambiente virtual e dependências
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuração do banco (`DATABASE_URL`)
Crie o arquivo `.env` a partir do modelo:
```bash
cp .env.example .env
```

* **Opção A — SQLite (padrão no `.env.example`):**
  ```env
  DATABASE_URL=sqlite:///./database.db
  ```
* **Opção B — PostgreSQL (com Docker Compose):**
  Suba o container definido em `docker-compose.yaml`:
  ```bash
  docker compose up -d
  ```
  E configure no `.env`:
  ```env
  DATABASE_URL=postgresql+psycopg://eventos:eventos@localhost:5432/gestao_eventos
  ```

### 3. Migrações com Alembic
Para criar/atualizar todas as tabelas no banco configurado em `DATABASE_URL`:
```bash
alembic upgrade head
```
O histórico inclui a migração inicial de criação do esquema (`2a32ba21db51`) e a migração incremental que adiciona `carga_horaria` à tabela `atividades` (`13f70167bde3`).

### 4. Povoamento inicial (Seed)
```bash
python -m scripts.seed
```
O script é idempotente e insere eventos, locais, palestrantes, 12 participantes, atividades, inscrições e presenças respeitando todas as restrições do modelo.

### 5. Subir a aplicação
```bash
uvicorn main:app --reload
```
Documentação interativa disponível em: `http://localhost:8000/docs`

---

## Endpoints Principais

### CRUD por recurso (`offset` e `limit` em todas as listagens)
* **Locais (`/locais`):** `POST /locais/`, `GET /locais/`, `GET /locais/{id}`, `PATCH /locais/{id}`, `DELETE /locais/{id}`
* **Eventos (`/eventos`):** `POST /eventos/`, `GET /eventos/`, `GET /eventos/{id}`, `PATCH /eventos/{id}`, `POST /eventos/{id}/cancelar`, `DELETE /eventos/{id}`
* **Participantes (`/participantes`):** `POST /participantes/`, `GET /participantes/`, `GET /participantes/{id}`, `PATCH /participantes/{id}`, `DELETE /participantes/{id}`
* **Palestrantes (`/palestrantes`):** `POST /palestrantes/`, `GET /palestrantes/`, `GET /palestrantes/{id}`, `PATCH /palestrantes/{id}`, `DELETE /palestrantes/{id}`
* **Atividades (`/atividades`):** `POST /atividades/`, `GET /atividades/`, `GET /atividades/{id}`, `PATCH /atividades/{id}`, `DELETE /atividades/{id}`
* **Inscrições (`/inscricoes`):** `POST /inscricoes/`, `GET /inscricoes/`, `GET /inscricoes/{id}`, `PATCH /inscricoes/{id}/status`, `GET /inscricoes/{id}/presenca`, `DELETE /inscricoes/{id}`
* **Presenças (`/presencas`):** `POST /presencas/`, `GET /presencas/`, `GET /presencas/{id}`, `DELETE /presencas/{id}`

### Filtros Disponíveis (aplicados diretamente no SQL)
* `GET /eventos/`: `status`, `tipo`, `nome`, `data_de`, `data_ate`
* `GET /locais/`: `tipo`, `ativo`, `nome`, `capacidade_min`
* `GET /participantes/`: `nome`, `ativo`, `instituicao`
* `GET /palestrantes/`: `nome`, `area_atuacao`
* `GET /atividades/`: `status`, `tipo`, `evento_id`, `local_id`, `com_vagas`, `nome`
* `GET /inscricoes/`: `status`, `participante_id`, `atividade_id`, `evento_id`
* `GET /presencas/`: `inscricao_id`, `atividade_id`, `metodo`

### Consultas Específicas e Estatísticas
* **Relacionamentos (F10):**
  * `GET /eventos/{evento_id}/atividades` — programação paginada de um evento com `vagas_disponiveis`.
  * `GET /palestrantes/{palestrante_id}/atividades` — atividades conduzidas pelo palestrante (N:N).
  * `GET /atividades/{atividade_id}/inscricoes` — inscritos de uma atividade com filtro opcional de `status`.
  * `GET /inscricoes/{inscricao_id}/presenca` — consulta o check-in vinculado à inscrição (1:1).
* **Consultas complexas (F11):**
  * `GET /participantes/{participante_id}/programacao` — cruza `Inscricao`, `Atividade`, `Local` e `Presenca`, com filtros opcionais por `evento_id` e intervalo (`inicio_de`, `inicio_ate`), ordenado por horário.
  * `GET /consultas/ocupacao-atividades` — executa `JOIN` entre `Atividade`, `Evento`, `Local` e `OUTER JOIN` com `Inscricao` e `Presenca`, agrupando por atividade com filtros (`evento_id`, `tipo`, `inicio_de`, `inicio_ate`, `apenas_com_vagas`, `apenas_sem_inscritos`).
* **Estatísticas (F12):**
  * `GET /estatisticas` — calcula totais (`COUNT`), soma e média de capacidade (`SUM`, `AVG`), taxa de ocupação, taxa de presença e agrupamentos (`GROUP BY`) por tipo de atividade, status de inscrição e resumo por evento.

---

## Regras de Negócio e Funcionalidade Específica do Tema

### Funcionalidade Específica (Tema 5)
* **Controle de inscrições considerando o limite de vagas das atividades:**
  * Ao solicitar `POST /inscricoes/`, o serviço contabiliza no banco as inscrições não canceladas da atividade (`status != cancelada`) e compara com `atividade.capacidade`. Se atingir o limite, a API bloqueia a operação retornando **HTTP 409**.
  * Ao reativar uma inscrição cancelada (`PATCH /inscricoes/{id}/status`), a disponibilidade de vaga é verificada novamente.
  * Não é permitido criar atividade com `capacidade` maior que a do `Local`, nem reduzir a `capacidade` da atividade abaixo do número de inscritos ativos.
  * As listagens e detalhes de atividades retornam `vagas_disponiveis` atualizado a partir do banco e permitem filtrar por `com_vagas=true|false`.

### Demais Regras de Negócio
1. **Unicidade de inscrição:** impede que um participante ativo se inscreva duas vezes na mesma atividade (permitindo apenas reativação caso a anterior esteja cancelada e haja vaga).
2. **Integridade de período e conflito de local:** uma atividade só pode ser agendada dentro do intervalo `[data_inicio, data_fim]` do evento, em um local ativo e sem sobreposição de horário com outra atividade no mesmo local.
3. **Bloqueio de entidades inativas/canceladas:** participantes inativos não podem se inscrever nem registrar presença; eventos e atividades cancelados não aceitam inscrições nem check-in.
4. **Check-in exclusivo (1:1):** presença só é registrada para inscrições confirmadas em atividades não canceladas e uma única vez por inscrição; inscrições com presença registrada não podem ser canceladas nem excluídas.
5. **Cancelamento em cascata lógica:** `POST /eventos/{id}/cancelar` cancela o evento, suas atividades e inscrições vinculadas preservando o histórico.
6. **Exclusão segura:** rotas `DELETE` bloqueiam a remoção quando há registros dependentes (atividades, inscrições ou palestras vinculadas), orientando a desativação/cancelamento quando aplicável.
