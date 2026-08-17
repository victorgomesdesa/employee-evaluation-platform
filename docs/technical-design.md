# Design Técnico: Plataforma de Avaliação de Funcionários

Documentação de arquitetura anterior ao desenvolvimento. Este documento descreve **como** o sistema é
construído e **por que** cada decisão foi tomada.

Os critérios funcionais e cenários de teste detalhados estão documentados em
[`user-stories.md`](./user-stories.md).

---

## 1. Visão Geral

Uma aplicação web onde um líder visualiza sua equipe, subordinados diretos e indiretos, e registra
avaliações ponderadas de desempenho, no máximo uma por funcionário por semana.

O sistema resolve três problemas centrais:

1. **Hierarquia recursiva**, descobrir toda a subárvore de um líder a partir de uma tabela de
   ligação, e não apenas seus reportes diretos.
2. **Autorização por hierarquia**, garantir que um líder só alcance quem está abaixo dele, nunca a
   si mesmo, pares ou superiores.
3. **Unicidade semanal sob concorrência**, impedir avaliações duplicadas mesmo com requisições
   simultâneas.

| Camada | Tecnologia |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL |

---

## 2. Arquitetura

Backend em camadas, com a responsabilidade de cada uma bem delimitada:

```
React Frontend
      │  HTTP (JSON)
      ▼
Evaluation API          camada HTTP: desserialização, schema, códigos de status
      ▼
Evaluation Service      regras de negócio: autorização, validações, cálculo
      ├──────────────► Hierarchy Service      resolução recursiva da hierarquia
      └──────────────► Evaluation Repository  acesso a dados e transações
                              ▼
                        PostgreSQL
```

Princípios que orientam a divisão:

- **A API não decide regra de negócio.** Ela traduz resultado de domínio em código HTTP.
- **O `EvaluationService` é a única autoridade.** Autorização, limite semanal, validação de respostas
  e cálculo da nota acontecem aqui, nunca no cliente.
- **O `EvaluationRepository` concentra transações.** Nenhuma outra camada abre ou confirma
  transação.
- **O `HierarchyService` isola a recursão.** A consulta recursiva fica em um único lugar, reutilizada
  por listagem e por autorização.

---

## 3. Decisões Técnicas

### 3.1 Identificação do líder ativo

Não há autenticação. O líder ativo é escolhido no cliente e enviado no cabeçalho `X-Leader-Id`.

Trata-se de um substituto deliberado para o escopo do desafio. **Toda regra de autorização continua
sendo aplicada pelo backend**, o cliente escolhe quem afirma ser, mas não escolhe o que pode fazer.
Em produção, essa identidade viria de uma sessão ou token autenticado, e apenas a origem do
`evaluatorId` mudaria; as validações permaneceriam idênticas.

O seletor exibe apenas funcionários que possuem ao menos um subordinado, no seed, sete deles. Um
funcionário folha não é inválido: se seu id for enviado diretamente, a listagem responde `200 OK` com
lista vazia.

### 3.2 Resolução da hierarquia

A hierarquia vive em `LeaderLead`, uma tabela de ligação entre dois funcionários. Um líder alcança o
**fechamento transitivo** dessa relação, não apenas suas linhas diretas.

A resolução usa uma CTE recursiva:

```sql
WITH RECURSIVE subtree AS (
    SELECT lead_id, 1 AS depth
      FROM leader_lead
     WHERE leader_id = :leader_id
    UNION ALL
    SELECT ll.lead_id, s.depth + 1
      FROM leader_lead ll
      JOIN subtree s ON ll.leader_id = s.lead_id
)
SELECT * FROM subtree;
```

Essa consulta atende ao seed válido fornecido, cujo organograma deve ser acíclico. Proteção contra
dados cíclicos exigiria detecção explícita por caminho ou suporte como `CYCLE`; isso está
deliberadamente fora do escopo do produto.

O `depth` retornado é relativo ao líder ativo e distingue subordinados **diretos** (`depth = 1`) de
**indiretos** (`depth > 1`). Ele não é o `evaluatorDepth` usado na seleção da avaliação principal.
Na premissa A-2, `evaluatorDepth` é a profundidade organizacional global, medida desde a raiz da
hierarquia e independente do líder ativo.

A mesma consulta serve à autorização: um funcionário só é acessível se estiver na subárvore do líder
ativo. Fora dela, pares, superiores ou o próprio líder, a resposta é `403 Forbidden`.

### 3.3 Modelo de avaliações

Uma `Evaluation` representa o ato de um avaliador avaliar um funcionário em uma semana, e agrega seis
`EvaluationAnswer`, uma por pergunta.

Duas associações **distintas** ligam `Evaluation` a `Employee`: `evaluatorId` (quem avaliou) e
`employeeId` (quem foi avaliado). São chaves estrangeiras separadas e nunca devem ser tratadas como
uma única relação.

As seis perguntas são dados fixos de seed. Não existe tela de configuração de perguntas, e a soma dos
pesos igual a `100` é um invariante do seed, não uma regra validada em tempo de execução.

### 3.4 Limite semanal

Uma avaliação por par avaliador e funcionário por semana. **Líderes diferentes podem avaliar o mesmo
funcionário na mesma semana**, o limite é por par, não por funcionário.

A regra é aplicada em dois lugares, de propósito:

| Camada | Papel |
|---|---|
| `EvaluationService` | Consulta prévia que produz um `409 Conflict` com mensagem útil |
| Constraint `UNIQUE(evaluatorId, employeeId, weekReference)` | Garante a integridade sob concorrência |

A validação de aplicação existe pela mensagem de erro; a constraint existe pela corrida. Ver
[§3.8](#38-concorrência-e-atomicidade).

### 3.5 Cálculo da nota

```
totalScore = Σ(score × weight) / 100
```

Cada `score` é um inteiro de 1 a 4; os pesos somam 100. O resultado é `DECIMAL(4,2)` e está sempre em
`[1.00, 4.00]`.

**O cálculo é exclusivo do backend.** O DTO de requisição não possui campo `totalScore`, e campos
desconhecidos no corpo são rejeitados com `422 Unprocessable Entity`. O cliente envia respostas; a
nota é derivada.

`EvaluationAnswer.weight` guarda o peso vigente no momento do envio. Esse snapshot protege avaliações
históricas de qualquer mudança futura no seed: a interpretação de uma avaliação antiga não muda
retroativamente.

### 3.6 Imutabilidade

Uma avaliação enviada não pode ser alterada nem excluída. Não existe rota `PUT`, `PATCH` ou `DELETE`
para `Evaluation` ou `EvaluationAnswer` em nenhuma camada.

Isso mantém o histórico auditável e é o que torna o snapshot de peso ([§3.5](#35-cálculo-da-nota))
significativo.

### 3.7 Avaliação principal

Quando existe mais de uma avaliação válida para o mesmo funcionário, a exibida como principal é
escolhida por uma ordenação em três níveis:

```sql
ORDER BY
    week_reference  DESC,
    evaluator_depth ASC,
    created_at      DESC
LIMIT 1
```

1. Semana mais recente que possua avaliação.
2. Dentro dessa semana, o avaliador de maior hierarquia, menor `evaluatorDepth`.
3. Em empate de profundidade, o `createdAt` mais recente.

Nesse comparador, `evaluatorDepth` é a profundidade organizacional global desde a raiz. Não se trata
do `depth` relativo retornado pela consulta de subordinados do líder ativo.

A recência é decidida **antes** da hierarquia: uma avaliação antiga de um avaliador mais alto nunca
substitui uma avaliação mais recente.

**Nenhuma avaliação é descartada.** Escolher uma principal é uma decisão de exibição; todas
permanecem armazenadas e inalteradas.

Esta é uma interpretação do requisito ambíguo *"sempre priorizando o avaliador de maior hierarquia"*,
registrada como premissa A-2 em [`user-stories.md`](./user-stories.md).

### 3.8 Concorrência e atomicidade

**Concorrência.** Duas requisições idênticas simultâneas passam pela verificação de aplicação antes
que qualquer uma grave. Só a constraint `UNIQUE` do banco impede a duplicata: uma obtém
`201 Created`, a outra `409 Conflict`, e exatamente uma linha existe.

**Atomicidade.** A avaliação e suas seis respostas são gravadas na mesma transação:

```
BEGIN
  INSERT INTO evaluation (...)
  INSERT INTO evaluation_answer (...) × 6
COMMIT
```

Se a inserção das respostas falhar, o `ROLLBACK` não deixa nenhuma `Evaluation` órfã. Uma avaliação
sem respostas seria um registro sem significado, a nota não poderia ser reconstruída.

---

## 4. Modelo de Dados

```
Employee 1 ──── 0..* LeaderLead        (papéis: leader, subordinate)
Employee 1 ──── 0..* Evaluation        (papel: evaluator)
Employee 1 ──── 0..* Evaluation        (papel: evaluatedEmployee)
Evaluation 1 ──◆ 6 EvaluationAnswer (composição após o envio)
EvaluationQuestion 1 ──── 0..* EvaluationAnswer
```

| Entidade | Atributos | Restrições |
|---|---|---|
| `Employee` | `id`, `name`, `email`, `positionName` | `email` único |
| `LeaderLead` | `leaderId`, `leadId` | PK composta; `leaderId ≠ leadId` |
| `Evaluation` | `id`, `evaluatorId`, `employeeId`, `createdAt`, `weekReference`, `totalScore` | `UNIQUE(evaluatorId, employeeId, weekReference)`; imutável |
| `EvaluationAnswer` | `id`, `evaluationId`, `questionId`, `score`, `weight` | `score` entre 1 e 4; `weight` é snapshot |
| `EvaluationQuestion` | `id`, `text`, `weight`, `displayOrder` | invariante do seed: soma dos pesos = 100 |

`weekReference` é a segunda-feira da semana ISO-8601, armazenada como `DATE`.

---

## 5. Fluxo de Avaliação

Ordem das etapas ao enviar uma avaliação. Cada guarda interrompe o fluxo sem gravar nada.

| # | Etapa | Falha |
|---|---|---|
| 1 | Frontend coleta seis respostas, inteiros de 1 a 4 | Não aplicável |
| 2 | `POST /api/evaluations` com `X-Leader-Id` | `400` se o cabeçalho for inválido |
| 3 | Autorização por hierarquia, consulta recursiva | `403 Forbidden` |
| 4 | Verificação do limite semanal | `409 Conflict` |
| 5 | Validação das respostas, presença e faixa | `422 Unprocessable Entity` |
| 6 | Cálculo da nota ponderada | Não aplicável |
| 7 | Persistência atômica: `Evaluation` + 6 `EvaluationAnswer` | `ROLLBACK` |
| 8 | Retorno | `201 Created` |

As validações são ordenadas da mais barata e restritiva para a mais cara: autorização antes de
qualquer leitura de avaliação, e toda a validação antes de qualquer escrita.

---

## 6. API

As rotas que operam sob uma identidade ativa exigem o cabeçalho `X-Leader-Id`. As rotas públicas de
apoio à inicialização, `GET /api/leaders` e `GET /api/evaluation/questions`, não exigem esse
cabeçalho.

| Método | Rota | `X-Leader-Id` | Descrição |
|---|---|---|---|
| `GET` | `/api/leaders` | Não | Funcionários com ao menos um subordinado; permite escolher o líder inicial |
| `GET` | `/api/evaluation/questions` | Não | Seis perguntas fixas do seed, ordenadas por `displayOrder` |
| `GET` | `/api/me/subordinates` | Sim | Subárvore do líder ativo, com marcação `direct` / `indirect` |
| `POST` | `/api/evaluations` | Sim | Cria uma avaliação |
| `GET` | `/api/employees/{id}/evaluations/latest` | Sim | Avaliação principal ([§3.7](#37-avaliação-principal)) |

Os dados de perfil usados pelo frontend já fazem parte da resposta de `/api/me/subordinates`; não
há um endpoint separado de detalhes. O histórico de avaliações é opcional no desafio e não foi
exposto nesta implementação.

**Corpo de `POST /api/evaluations`:**

```json
{
  "employeeId": 10,
  "answers": [
    { "questionId": 1, "score": 4 }
  ]
}
```

Campos não definidos no schema, incluindo `totalScore`, `weight`, `weekReference` e `evaluatorId`
são rejeitados. Todos são derivados ou controlados pelo backend.

**Códigos de status:**

| Código | Significado |
|---|---|
| `200 OK` | Leitura bem-sucedida, inclusive resultado vazio |
| `201 Created` | Avaliação registrada |
| `400 Bad Request` | `X-Leader-Id` ausente, malformado ou inexistente |
| `403 Forbidden` | Funcionário existe, mas está fora da subárvore do líder |
| `404 Not Found` | Funcionário inexistente |
| `409 Conflict` | Já avaliado por este líder nesta semana |
| `422 Unprocessable Entity` | Respostas inválidas ou campo desconhecido |

`403` e `404` são distintos de propósito: sem autenticação real, ocultar quais ids existem não
protege nada.

---

## 7. Diagramas UML

Os diagramas são largos demais para garantir texto legível quando incorporados na largura padrão do
Markdown. Prefira abri-los em tamanho completo.

### Diagrama de Casos de Uso

[Visualizar em tamanho completo](./diagrams/01-use-case-diagram.svg)

Ator `Líder`, fronteira do sistema e as operações obrigatórias de *Avaliar subordinado*, ligadas por
`«include»`. As seis regras de negócio aparecem como notas UML.

### Diagrama de Classes

[Visualizar em tamanho completo](./diagrams/02-class-diagram.svg)

Modelo de domínio com multiplicidades, papéis de associação e restrições. Destaca as duas associações
distintas entre `Evaluation` e `Employee`.

### Diagrama de Sequência: Compacto

[Visualizar em tamanho completo](./diagrams/03-evaluation-sequence-compact.svg)

Cinco participantes. Mesmo fluxo do detalhado, com `Hierarchy Service` e `Evaluation Repository`
incorporados ao `Evaluation Service`. Melhor para uma leitura rápida.

### Diagrama de Sequência: Detalhado

[Visualizar em tamanho completo](./diagrams/03-evaluation-sequence-detailed.svg)

Sete participantes, com a separação completa de responsabilidades entre serviços e repositório.
Mostra as guardas `alt`, a transação `critical` e todos os retornos.

---

## 8. Premissas Técnicas

O enunciado deixa quatro pontos em aberto. Cada um é uma interpretação adotada para o desafio, não um
requisito fornecido. As premissas estão detalhadas e associadas a testes em
[`user-stories.md`](./user-stories.md).

| ID | Premissa |
|---|---|
| **A-1** | Semana = semana de calendário ISO-8601, de segunda a domingo, no fuso `America/Sao_Paulo` |
| **A-2** | *"Maior hierarquia"* = ordenação `weekReference DESC`, `evaluatorDepth ASC`, `createdAt DESC` |
| **A-3** | O seletor de líderes lista apenas funcionários com ao menos um subordinado |
| **A-4** | Não há autenticação; a identidade é fornecida pelo cliente e validada pelo backend |

### Fora do escopo

Perguntas configuráveis ou desativáveis, proteção contra enumeração de ids, identidade de líder por
aba do navegador, rate limiting, log de auditoria, exclusão lógica e paginação. Nenhum desses itens é
solicitado pelo desafio.

### Convenção de idioma

Documentação, interface e mensagens ao usuário em português do Brasil. Identificadores técnicos,
como classes, atributos, endpoints, serviços e nomes de banco, permanecem em inglês. `EvaluationQuestion.text`
preserva exatamente o texto fornecido pelo desafio e é exibido diretamente pela interface.
