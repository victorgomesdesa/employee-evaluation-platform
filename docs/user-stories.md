# Histórias de Usuário e Critérios de Aceitação

Documento complementar ao [`technical-design.md`](./technical-design.md). O design técnico descreve
**como** o sistema é construído; este documento define **o que ele deve fazer** e **como provamos
isso**.

Todo critério de aceitação é escrito para ser executável, e todo cenário de teste da
[§10](#10-cenários-de-teste-derivados) deriva de um deles. O escopo se limita ao que o desafio pede,
e a [§11.2](#112-fora-do-escopo-deliberadamente) registra o que foi considerado e deixado de fora.

---

## 1. Convenções

### 1.1 Formato dos critérios

Cada critério segue `Dado / Quando / Então`, redigido de forma que possa virar teste sem
reinterpretação. Um critério que não pode falhar não é um critério.

### 1.2 Vocabulário

| Termo | Definição |
|---|---|
| **Líder** | Funcionário que possui ao menos um subordinado e está selecionado como usuário ativo. |
| **Subordinado direto** | Registro em `LeaderLead` com `leaderId = <líder>`. |
| **Subordinado indireto** | Funcionário alcançável a partir do líder por dois ou mais saltos em `LeaderLead`. |
| **Subordinado** | Direto **ou** indireto. Nunca o próprio líder. |
| **Par** | Funcionário fora da subárvore do líder ativo que compartilha o mesmo líder. |
| **Profundidade** | Saltos a partir da raiz da hierarquia. Menor profundidade = posição mais alta na organização. |
| **Avaliação principal** | A avaliação exibida por "visualizar avaliação principal" quando existe mais de uma, ver [A-2](#2-premissas). |
| **`weekReference`** | A segunda-feira da semana ISO-8601 em que a avaliação foi criada, ver [A-1](#2-premissas). |
| **`totalScore`** | `Σ(score × weight) / 100`, `DECIMAL(4,2)`, sempre no intervalo `[1.00, 4.00]`. |

### 1.3 Níveis de teste

`U` unitário (lógica pura, sem I/O) · `I` integração (API + PostgreSQL real) · `E` ponta a ponta
(navegador).

---

## 2. Premissas

O desafio deixa quatro pontos em aberto. Cada um é resolvido aqui, marcado como **interpretação
nossa** e não como requisito fornecido, e sustentado por um teste.

**A-1: Uma semana é uma semana de calendário ISO-8601**, de segunda a domingo, avaliada no fuso
horário da aplicação `America/Sao_Paulo`. O enunciado diz apenas "uma avaliação por semana", sem
definir quando a semana começa. Um limite de calendário fixo é verificável (T-04.5); uma janela móvel
de 7 dias faria a regra depender do horário do envio.

**A-2: "Sempre priorizando o avaliador de maior hierarquia" é interpretado como uma ordenação em
três níveis.** O requisito é ambíguo; esta é uma interpretação adotada para o desafio, não uma regra
explicitamente definida no enunciado.

A seleção ocorre nesta ordem:

1. **`weekReference` mais recente** que possua alguma avaliação para o funcionário.
2. Dentro dessa semana, a avaliação do avaliador **de maior hierarquia**, ou seja, o de **menor**
   `evaluatorDepth`.
3. Em empate de profundidade, vence o **`createdAt` mais recente**.

`evaluatorDepth` representa a profundidade organizacional global desde a raiz da hierarquia. Ele é
independente do líder ativo e não deve ser confundido com o `depth` relativo da consulta de
subordinados, em que `depth = 1` significa subordinado direto e `depth > 1`, indireto.

```sql
ORDER BY
    week_reference  DESC,
    evaluator_depth ASC,
    created_at      DESC
LIMIT 1
```

Duas consequências que vale explicitar:

- A regra de hierarquia se aplica **dentro** da semana mais recente. Ela nunca promove uma avaliação
  antiga sobre uma mais nova, a recência é decidida primeiro.
- **Todas as avaliações permanecem armazenadas.** Escolher uma principal nunca apaga, altera ou
  oculta outra avaliação.

**A-3: O seletor de líderes lista apenas funcionários que lideram alguém.** O enunciado pede uma
forma de alternar entre *líderes*; um funcionário sem liderados não é líder e não teria nada a
exibir. A API continua se comportando corretamente caso o id de um funcionário folha seja enviado
diretamente (AC-02.4).

**A-4: Não há autenticação.** A identidade ativa é escolhida no cliente e enviada em
`X-Leader-Id`. Trata-se de um substituto deliberado para o desafio. Toda regra de autorização
continua sendo aplicada pelo backend, que é justamente o ponto demonstrado.

---

## 3. Fixture de Testes

A hierarquia completa do seed fornecido, 20 funcionários, dos quais 7 lideram alguém.

```
Alice (CEO)                              profundidade 0
├── Bob (CTO)                            profundidade 1
│   ├── David (Engineering Manager)      profundidade 2
│   │   ├── Henry (Senior Engineer)      profundidade 3
│   │   │   ├── James (Engineer)         profundidade 4
│   │   │   └── Karen (Engineer)         profundidade 4
│   │   └── Liam (Engineer)              profundidade 3
│   ├── Eva (Engineering Manager)        profundidade 2
│   │   ├── Isabelle (Senior Engineer)   profundidade 3
│   │   ├── Noah (Data Analyst)          profundidade 3
│   │   └── Mia (Data Engineer)          profundidade 3
│   ├── Grace (UX)                       profundidade 2
│   ├── Quinn (DevOps)                   profundidade 2
│   └── Paul (QA)                        profundidade 2
├── Carol (CFO)                          profundidade 1
│   ├── Rachel (Finance Analyst)         profundidade 2
│   └── Samuel (Finance Analyst)         profundidade 2
├── Frank (Product Manager)              profundidade 1
│   └── Olivia (QA)                      profundidade 2
└── Tina (HR)                            profundidade 1
```

**Líderes, os únicos itens que o seletor pode exibir (7):**
`Alice`, `Bob`, `Carol`, `David`, `Eva`, `Frank`, `Henry`.

**Funcionários folha, nunca aparecem no seletor (13):**
`Grace`, `Isabelle`, `James`, `Karen`, `Liam`, `Mia`, `Noah`, `Olivia`, `Paul`, `Quinn`, `Rachel`,
`Samuel`, `Tina`.

### 3.1 Tamanhos das Subárvores

| Líder | Total | Diretos | Indiretos |
|---|---:|---|---|
| `Alice` | 19 | `Bob`, `Carol`, `Frank`, `Tina` | os outros 15 |
| `Bob` | **12** | `David`, `Eva`, `Grace`, `Paul`, `Quinn` | `Henry`, `Isabelle`, `James`, `Karen`, `Liam`, `Mia`, `Noah` |
| `David` | 4 | `Henry`, `Liam` | `James`, `Karen` |
| `Eva` | 3 | `Isabelle`, `Mia`, `Noah` | Nenhum |
| `Henry` | 2 | `James`, `Karen` | Nenhum |
| `Carol` | 2 | `Rachel`, `Samuel` | Nenhum |
| `Frank` | 1 | `Olivia` | Nenhum |

### 3.2 Relações Utilizadas pelos Cenários

| Caso | Par |
|---|---|
| Direto | `Bob → David` |
| Indireto (2 saltos) | `Bob → Henry` |
| Indireto profundo (3 saltos) | `Bob → James` |
| Par | `David ↔ Eva` (ambos reportam a `Bob`) |
| Superior | `David → Bob` |
| Próprio | `David → David` |
| Folha, sem liderados | `James` |
| Ordem de profundidade para A-2 | `Bob` (1) está acima de `David` (2); ambos podem avaliar `Henry` |

> **Sobre o passo 3 de A-2.** Os avaliadores válidos de um funcionário são exatamente seus
> ancestrais e, em uma árvore, cada ancestral está em uma profundidade distinta, portanto, com este
> seed, um empate de profundidade não ocorre. O critério de desempate continua importando:
> `LeaderLead` permite que um funcionário tenha mais de um líder, então a ordenação precisa ser total
> e determinística independentemente dos dados. Por isso ele é verificado por um teste de integração
> da ordenação (T-05.4), com dados controlados para representar o empate.

### 3.3 Perguntas do Seed

As seis perguntas são dados fixos de seed, fornecidos pelo desafio. `EvaluationQuestion.text`
armazena exatamente o texto abaixo, que é o mesmo exibido pela interface, ver
[§11.4](#114-política-de-idioma).

| `displayOrder` | Pergunta | `weight` |
|---:|---|---:|
| 1 | Entrega de Resultados | 25 |
| 2 | Execução e Qualidade do Trabalho | 20 |
| 3 | Capacidade de Aprendizado e Desenvolvimento | 20 |
| 4 | Resolução de Problemas e Pensamento Crítico | 15 |
| 5 | Colaboração, Influência e Liderança | 10 |
| 6 | Visão Estratégica e Potencial de Crescimento | 10 |
| | **Total** | **100** |

`Σ weight = 100` é um invariante do seed, verificado por T-04.14.

---

## 4. US-01: Alterar líder ativo

> **Como** usuário da demonstração,
> **quero** escolher como qual líder estou atuando,
> **para** explorar a hierarquia a partir de diferentes pontos de vista.

**AC-01.1**: Dado que a aplicação está aberta, quando a lista de líderes for solicitada, então
exatamente os sete funcionários que possuem ao menos um subordinado ficam selecionáveis, e os treze
funcionários folha estão ausentes. *(A-3)*

**AC-01.2**: Dado que o líder `Bob` está selecionado, quando a página for recarregada, então `Bob`
continua sendo o líder ativo.

**AC-01.3**: Dado que o líder `Bob` está selecionado, quando o líder for alterado para `David`,
então todos os dados exibidos passam para o escopo de `David` e nenhum dado do escopo de `Bob`
permanece visível.

---

## 5. US-02: Visualizar subordinados

> **Como** líder,
> **quero** ver os funcionários que se reportam a mim direta ou indiretamente,
> **para** saber por quem sou responsável na avaliação.

**AC-02.1**: Dado o líder `Bob`, quando a lista de subordinados for solicitada, então ela contém
exatamente 12 funcionários: `David`, `Eva`, `Grace`, `Paul`, `Quinn`, `Henry`, `Isabelle`, `James`,
`Karen`, `Liam`, `Mia`, `Noah`, a subárvore inteira, não apenas os reportes diretos.

**AC-02.2**: Dado o líder `Bob`, quando a lista de subordinados for solicitada, então `David`,
`Eva`, `Grace`, `Paul`, `Quinn` são marcados como `direct` e `Henry`, `Isabelle`, `James`, `Karen`,
`Liam`, `Mia`, `Noah` como `indirect`.

**AC-02.3**: Dado o líder `David`, quando a lista de subordinados for solicitada, então ela contém
exatamente `Henry`, `Liam`, `James`, `Karen`, e exclui o próprio `David`, seus pares `Eva`, `Grace`,
`Paul`, `Quinn`, e seus superiores `Bob` e `Alice`.

**AC-02.4**: Dado que `X-Leader-Id` identifica `James`, um funcionário folha, quando a lista de
subordinados for solicitada, então a API responde `200 OK` com lista vazia. Um funcionário folha não
é inválido apenas por não aparecer no seletor. *(A-3)*

---

## 6. US-03: Visualizar detalhes do subordinado

> **Como** líder,
> **quero** abrir o perfil de um subordinado,
> **para** saber quem estou prestes a avaliar.

**AC-03.1**: Dado o líder `Bob` e o subordinado `James`, quando a subárvore for solicitada, então o
registro de `James` contém `name`, `email` e `positionName`, e a interface usa esses dados para exibir
seu perfil sem uma segunda rota de detalhes.

**AC-03.2**: Dado o líder `David`, quando uma operação protegida de avaliação for solicitada para
`Eva` (par), `Bob` (superior) ou `David` (ele próprio), então a API responde `403 Forbidden`.

**AC-03.3**: Dado qualquer líder, quando uma operação protegida de avaliação for solicitada para um
id de funcionário inexistente, então a API responde `404 Not Found`.

**AC-03.4**: Dada uma rota protegida, quando `X-Leader-Id` estiver ausente ou malformado, então a API
responde `400 Bad Request` sem precisar acessar o banco de dados.

**AC-03.5**: Dada uma rota protegida, quando `X-Leader-Id` for sintaticamente válido, mas apontar para
um funcionário inexistente, então a API responde `400 Bad Request`. A consulta de identidade pode
ocorrer, mas nenhuma operação de negócio sobre subordinados ou avaliações, nem qualquer escrita, é
executada.

---

## 7. US-04: Avaliar um subordinado

> **Como** líder,
> **quero** enviar uma avaliação ponderada de um subordinado,
> **para** que o desempenho dele fique registrado na semana.

História central. Os critérios estão agrupados pela validação que exercitam, espelhando os blocos
`alt` do diagrama de sequência detalhado.

### 7.1 Formulário

**AC-04.1**: Dado que o formulário de avaliação está aberto, quando ele for renderizado, então
exibe as seis perguntas do seed ordenadas por `displayOrder`, cada uma oferecendo apenas as opções
inteiras `1, 2, 3, 4`, e o botão de envio permanece desabilitado até que as seis sejam respondidas.

### 7.2 Validação de hierarquia

**AC-04.2**: Dado o líder `Bob`, quando uma avaliação for enviada para `James` (três saltos abaixo),
então ela é aceita com `201 Created`.

**AC-04.3**: Dado o líder `David`, quando uma avaliação for enviada para `Eva` (par), `Bob`
(superior) ou `David` (ele próprio), então a API responde `403 Forbidden` e nenhum registro de
`Evaluation` ou `EvaluationAnswer` é criado.

### 7.3 Limite semanal

**AC-04.4**: Dado que `Bob` já avaliou `David` na semana corrente, quando `Bob` enviar uma segunda
avaliação para `David` na mesma semana, então a API responde `409 Conflict` e a contagem armazenada
para esse par e semana permanece `1`.

**AC-04.5**: Dado que `Bob` já avaliou `David` nesta semana, quando `Alice` avaliar `David` na mesma
semana, então a avaliação é aceita com `201 Created`. O limite é por par avaliador e funcionário, não
por funcionário.

**AC-04.6**: Dado que `Bob` avaliou `David` em um domingo, quando `Bob` avaliar `David` na
segunda-feira seguinte, então a avaliação é aceita com `201 Created`, porque a segunda-feira inicia
uma nova semana ISO. *(A-1)*

**AC-04.7**: Dadas duas requisições de avaliação idênticas para o mesmo par e semana chegando de
forma concorrente, quando ambas forem processadas, então exatamente uma é bem-sucedida com
`201 Created`, a outra recebe `409 Conflict`, e existe exatamente um registro de `Evaluation`.

### 7.4 Validação das respostas

**AC-04.8**: Dada uma requisição de avaliação, quando alguma resposta tiver `score` fora do
intervalo `1..4`, não for inteiro ou for `null`, então a API responde `422 Unprocessable Entity` e
nada é persistido.

**AC-04.9**: Dada uma requisição de avaliação, quando faltar alguma pergunta, ou algum `questionId`
estiver duplicado ou for desconhecido, então a API responde `422 Unprocessable Entity` e nada é
persistido.

**AC-04.10**: Dado que o corpo da requisição traz um campo não definido no schema, `totalScore`,
`weight`, `weekReference`, `evaluatorId` ou qualquer outro, quando ela for processada, então a API
responde `422 Unprocessable Entity`. O DTO de requisição é exatamente:

```json
{
  "employeeId": 10,
  "answers": [
    { "questionId": 1, "score": 4 }
  ]
}
```

Todo o restante é derivado ou controlado pelo backend.

### 7.5 Cálculo da nota

**AC-04.11**: Dadas as respostas `[4, 3, 4, 2, 3, 1]` sobre os pesos do seed
`[25, 20, 20, 15, 10, 10]`, quando a avaliação for armazenada, então `totalScore = 3.10`.

> `(4×25 + 3×20 + 4×20 + 2×15 + 3×10 + 1×10) / 100 = 310 / 100 = 3.10`

**AC-04.12**: Dado que todas as respostas são `4`, então `totalScore = 4.00`. Dado que todas as
respostas são `1`, então `totalScore = 1.00`. Esses são os únicos limites alcançáveis.

### 7.6 Persistência e imutabilidade

**AC-04.13**: Dada uma avaliação válida com seis respostas, quando ela for armazenada, então existe
um registro de `Evaluation` e seis de `EvaluationAnswer`, e cada resposta carrega o `weight` da sua
pergunta no momento do envio.

**AC-04.14**: Dado que a inserção de `EvaluationAnswer` falha, quando a transação for resolvida,
então é feito `ROLLBACK` e nenhum registro de `Evaluation` permanece, a avaliação e suas respostas
são gravadas juntas ou não são gravadas.

**AC-04.15**: Dada uma avaliação armazenada, quando `PUT`, `PATCH` ou `DELETE` for tentado sobre
ela, então nenhuma rota desse tipo existe e o registro permanece inalterado.

---

## 8. US-05: Visualizar avaliação principal

> **Como** líder,
> **quero** ver a avaliação atual de um subordinado,
> **para** saber como ele está.

> Regido por **A-2**. O líder enxerga avaliações de qualquer pessoa da sua subárvore,
> **independentemente de quem as tenha feito**. A-2 decide apenas qual delas é exibida como principal
> quando há mais de uma.

**AC-05.1**: Dado que `Bob` avaliou `Henry` na semana W1 e `David` avaliou `Henry` na semana
posterior W2, quando a avaliação principal de `Henry` for solicitada, então é retornada a **avaliação
de `David` em W2**. A recência é decidida antes da hierarquia, portanto a avaliação mais antiga de W1
não é promovida mesmo com `Bob` estando acima de `David`. *(A-2, passo 1)*

**AC-05.2**: Dado que `Bob` (profundidade 1) e `David` (profundidade 2) avaliaram `Henry` na mesma
semana W2, quando a avaliação principal de `Henry` for solicitada, então é retornada a **avaliação de
`Bob`**, porque `Bob` está mais alto na organização, independentemente de qual dos dois seja o líder
ativo. *(A-2, passo 2)*

**AC-05.3**: Dado que existem várias avaliações para o mesmo funcionário, quando uma for
selecionada como principal, então todas as demais permanecem armazenadas e inalteradas. A seleção da
principal nunca apaga nem modifica outra avaliação.

**AC-05.4**: Dadas duas avaliações do mesmo funcionário e da mesma semana cujos avaliadores têm a
mesma profundidade, quando a principal for selecionada, então vence a de `createdAt` mais recente.
*(A-2, passo 3, requisito de ordenação total; ver a nota em
[§3.2](#32-relações-utilizadas-pelos-cenários))*

**AC-05.5**: Dado que ninguém nunca avaliou `Liam`, quando a avaliação principal for solicitada,
então a resposta é `200 OK` com resultado vazio e a interface exibe um estado vazio.

**AC-05.6**: Dado o líder `David`, quando a avaliação principal for solicitada para `Eva` (par),
`Bob` (superior) ou `David` (ele próprio), então a API responde `403 Forbidden`.

---

## 9. US-06: Visualizar histórico de avaliações *(escopo opcional)*

> **Como** líder,
> **quero** ver todas as avaliações de um subordinado ao longo do tempo,
> **para** acompanhar a evolução.

> Marcada como `«opcional»` no diagrama de casos de uso. Implementar apenas depois de US-01 … US-05
> concluídas. Nada
> nas histórias centrais depende da existência deste endpoint.

**AC-06.1**: Dado que `Henry` foi avaliado nas semanas W1, W2 e W3, quando o histórico for
solicitado, então as três avaliações são retornadas em ordem decrescente de `weekReference`.

**AC-06.2**: Dado que `Bob` e `David` avaliaram `Henry` na mesma semana, quando o histórico for
solicitado, então ambas as avaliações são retornadas, cada uma identificada por seu avaliador,
inclusive aquela que A-2 não selecionou como principal.

**AC-06.3**: Dado o líder `David`, quando o histórico for solicitado para `Eva` (par) ou `Bob`
(superior), então a API responde `403 Forbidden`.

---

## 10. Cenários de Teste Derivados

Cada cenário existe **por causa** do critério indicado na primeira coluna.

### 10.1 Identidade e hierarquia

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-01.1 | AC-01.1 | Conteúdo do seletor de líderes | I | Exatamente 7 líderes; as 13 folhas ausentes |
| T-01.2 | AC-01.2 | Selecionar `Bob` e recarregar | E | `Bob` continua ativo |
| T-01.3 | AC-01.3 | Alternar `Bob` → `David` | E | Lista passa aos 4 de `David`; nada de `Bob` permanece |
| T-02.1 | AC-02.1 | `subordinatesOf(Bob)` | I | Exatamente 12 funcionários |
| T-02.2 | AC-02.2 | Marcação de profundidade para `Bob` | I | 5 `direct`, 7 `indirect` |
| T-02.3 | AC-02.3 | `subordinatesOf(David)` | I | `Henry`, `Liam`, `James`, `Karen`; pares e superiores ausentes |
| T-02.4 | AC-02.4 | `subordinatesOf(James)` | I | `200 OK`, `[]` |

### 10.2 Controle de acesso

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-03.1 | AC-03.1 | `Bob` lista e abre `James` | I | `200 OK` + dados de perfil na subárvore |
| T-03.2 | AC-03.2 | `David` tenta avaliar ou consultar `Eva` / `Bob` / `David` | I | `403` em cada caso |
| T-03.3 | AC-03.3 | Operação protegida usa o id `999999` | I | `404` |
| T-03.4a | AC-03.4 | `X-Leader-Id` ausente ou malformado | I | `400`, sem acesso ao banco |
| T-03.4b | AC-03.5 | `X-Leader-Id` válido, mas funcionário inexistente | I | `400`; pode consultar a identidade, sem operação de negócio ou escrita |

### 10.3 Validações da avaliação

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-04.1 | AC-04.2 | `Bob` avalia `James` (3 saltos) | I | `201`, 1 avaliação + 6 respostas |
| T-04.2 | AC-04.3 | `David` avalia `Eva` / `Bob` / `David` | I | `403`, nenhum registro gravado |
| T-04.3 | AC-04.4 | Segundo envio, mesmo par e semana | I | `409`, contagem permanece `1` |
| T-04.4 | AC-04.5 | `Alice` avalia `David` na mesma semana | I | `201` |
| T-04.5 | AC-04.6 | Domingo e depois segunda-feira | I | `201`, nova semana ISO |
| T-04.6 | AC-04.7 | Duas requisições idênticas concorrentes | I | Exatamente um `201`, um `409`, 1 registro |

> **T-04.6 é o teste que justifica validar o limite semanal duas vezes.** Substitua o
> `existsForWeek` do service por um stub que retorna `false` nas duas requisições, anulando a
> validação de aplicação; assim, apenas a constraint `UNIQUE(evaluatorId, employeeId, weekReference)`
> pode impedir a duplicata. Se este teste continuar passando com a constraint removida, o teste está
> errado.

### 10.4 Respostas e cálculo da nota

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-04.7 | AC-04.8 | `score` = `0` / `5` / `2.5` / `"3"` / `null` | U | `422` em cada caso |
| T-04.8 | AC-04.9 | Cinco das seis perguntas respondidas | I | `422` |
| T-04.9 | AC-04.9 | `questionId` duplicado ou desconhecido | I | `422` |
| T-04.10 | AC-04.10 | Corpo inclui `totalScore`, `weight`, `weekReference` ou `evaluatorId` | I | `422` em cada caso |
| T-04.11 | AC-04.1 | Formulário oferece apenas `1..4`; envio bloqueado enquanto incompleto | E | Nenhum outro valor aceito |
| T-04.12 | AC-04.11 | `[4,3,4,2,3,1]` | U | `3.10` |
| T-04.13 | AC-04.12 | Todas `4` / todas `1` | U | `4.00` / `1.00` |
| T-04.14 | AC-04.11 | Pesos do seed somam 100 | U | Invariante válido |

### 10.5 Persistência e imutabilidade

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-04.15 | AC-04.13 | Envio válido | I | 1 + 6 registros; `weight` das respostas igual ao das perguntas |
| T-04.16 | AC-04.14 | Forçar falha na inserção das respostas | I | `ROLLBACK`; nenhum registro de `Evaluation` permanece |
| T-04.17 | AC-04.15 | `PUT` / `PATCH` / `DELETE` sobre uma avaliação | I | `404`/`405`; registro inalterado |

### 10.6 Seleção da avaliação principal

Os três casos de A-2, testados explicitamente.

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-05.1 | AC-05.1 | `Bob → Henry` em W1, `David → Henry` em W2 | I | A avaliação de `David` em **W2** é a principal, a semana mais recente vence a hierarquia |
| T-05.2 | AC-05.2 | `Bob → Henry` e `David → Henry`, ambos em W2 | I | A avaliação de `Bob` é a principal, a hierarquia vence dentro da semana |
| T-05.3 | AC-05.3 | Qualquer um dos cenários acima, inspecionando o armazenamento | I | Os dois registros presentes e inalterados |
| T-05.4 | AC-05.4 | Ordenação com duas entradas, mesma semana e mesmo `evaluatorDepth` | I | `createdAt` mais recente ordenado primeiro |
| T-05.5 | AC-05.5 | `Liam` nunca avaliado | I | `200`, resultado vazio |
| T-05.6 | AC-05.6 | `David` lê avaliação de `Eva` / `Bob` / `David` | I | `403` |

### 10.7 Histórico *(opcional)*

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-06.1 | AC-06.1 | Histórico de W1 a W3 | I | Ordem decrescente de `weekReference` |
| T-06.2 | AC-06.2 | Dois avaliadores, mesma semana | I | Ambas listadas, com o avaliador identificado |
| T-06.3 | AC-06.3 | Histórico de um par ou superior | I | `403` |

### 10.8 Jornada

| ID | Critério | Cenário | Nível | Esperado |
|---|---|---|---|---|
| T-E2E.1 | US-01 → US-05 | Escolher `Bob` → listar → abrir `Henry` → avaliar → ver avaliação principal | E | A nota exibida corresponde às respostas enviadas |
| T-E2E.2 | AC-04.4 | Avaliar o mesmo subordinado duas vezes na semana | E | Mensagem clara de "já avaliado nesta semana", sem stack trace |

---

## 11. Notas

### 11.1 Premissas e suas provas

| ID | Premissa | Provada por |
|---|---|---|
| A-1 | Semana = semana de calendário ISO-8601, `America/Sao_Paulo` | T-04.5 |
| A-2 | Principal = semana mais recente → avaliador de maior hierarquia → `createdAt` mais recente | T-05.1, T-05.2, T-05.4 |
| A-3 | O seletor de líderes lista apenas quem lidera alguém | T-01.1, T-02.4 |
| A-4 | Sem autenticação; identidade fornecida pelo cliente | Contexto para T-03.4a e T-03.4b |

### 11.2 Fora do escopo deliberadamente

Itens considerados e excluídos, para manter a lista de critérios restrita ao que será de fato
construído e testado.

1. **Perguntas configuráveis, editáveis ou desativáveis.** As seis perguntas e seus pesos são dados
   fixos de seed. `Σ weight = 100` é um invariante do seed, não uma regra a ser validada em tempo de
   execução.
2. **Proteção contra ciclos na consulta de hierarquia.** O seed fornecido representa um organograma
   válido e acíclico. A consulta recursiva é definida para esses dados. Detecção explícita por caminho
   ou `CYCLE` para dados malformados está fora do escopo; não se presume que `UNION` garanta término
   quando a tupla recursiva também carrega `depth`.
3. **Proteção contra enumeração de ids.** Sob A-4 o próprio chamador escolhe sua identidade, então
   ocultar quais ids existem não protege nada. Daí o `404` em AC-03.3.
4. **Identidade de líder por aba.** O `localStorage` é compartilhado entre abas; duas abas não podem
   atuar como líderes diferentes. Aceitável para uma demonstração.
5. **Rate limiting, log de auditoria, exclusão lógica, paginação.** Não solicitados.

### 11.3 Invariantes Técnicos

Decisões de modelagem que não são requisitos visíveis ao usuário e, por isso, não possuem critério de
aceitação próprio.

1. **`EvaluationAnswer.weight` é um snapshot histórico** do peso da pergunta no momento do envio.
   Protege as avaliações armazenadas de futuras mudanças de seed ou de dados sem tornar a
   configuração de perguntas parte do escopo da aplicação. Verificado estruturalmente por T-04.15 e
   documentado como `SNAPSHOT DE PESO` no diagrama de classes.
2. **`UNIQUE(evaluatorId, employeeId, weekReference)`** sustenta o limite semanal no nível do banco.
   Seu propósito é concorrência, não validação, ver T-04.6.
3. **Avaliações são imutáveis.** Nenhuma rota de alteração ou exclusão é exposta em qualquer camada.

### 11.4 Política de idioma

A documentação, os textos da interface e as mensagens apresentadas ao usuário são escritos em
português do Brasil, acompanhando o idioma do desafio original.

Identificadores técnicos, como classes, atributos, endpoints, serviços, funções e nomes de banco,
permanecem em inglês (`Employee`, `EvaluationService`, `week_reference`, `POST /api/evaluations`,
`X-Leader-Id`). Mensagens de commit também seguem em inglês.

`EvaluationQuestion.text` preserva exatamente o texto fornecido pelo desafio e é exibido diretamente
pela interface. Não existe uma camada separada de tradução das perguntas.
