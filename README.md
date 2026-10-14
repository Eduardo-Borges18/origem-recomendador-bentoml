# Origem Recomenda

Mockup do módulo de recomendação de produtos do marketplace **Origem**. Recebe um produto ou usuário como contexto e devolve até oito produtos públicos ordenados. Trilha A da AV1 prática: serviço em BentoML, com catálogo sintético de 12 produtos. O ranqueamento é uma regra determinística, conforme a especificação da AV1; não usa modelo treinado nem dados reais.

**Grupo 3 — Squad Origem** · Turma **AdsA-Regular**  
**Integrantes:** Eduardo Borges Cordeiro de Oliveira Carlos; Eliziane Mota; Pedro Iranildo; Ricardo Severiano; Sérgio Chousinho.

## Estrutura

- `service.py`: endpoint HTTP, validação, elegibilidade, ordenação, fallback e log operacional.
- `catalogo.json`: 12 produtos fictícios, incluindo exemplos inativo e sem estoque.
- `requirements.txt`: dependências Python.

## Instalação e execução

Requisitos: Python 3.11 ou superior e acesso à internet apenas para instalar as dependências. Não é necessária chave de API, banco de dados ou conexão com o Origem.

Em Linux/macOS:

```bash
git clone https://github.com/Eduardo-Borges18/origem-recomendador-bentoml.git
cd origem-recomendador-bentoml
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bentoml serve service:RecomendadorOrigem --port 3000
```

Em Windows PowerShell, após clonar e entrar na pasta:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
bentoml serve service:RecomendadorOrigem --port 3000
```

O serviço deve ficar em `http://localhost:3000`. Em outro terminal, use os comandos abaixo. No PowerShell, substitua `curl` por `curl.exe`.

## Ambiente de validação

O serviço foi instalado e executado a partir do repositório em Windows, com as seguintes versões:

| Componente | Versão verificada |
|---|---|
| Python | 3.11.9 |
| BentoML | 1.4.39 |
| FastAPI | 0.143.0 |

Validação registrada por **Byteric** em **13/10/2026**, sobre o código do commit [`deb1ad8`](https://github.com/Eduardo-Borges18/origem-recomendador-bentoml/commit/deb1ad89774d3be5a218b2749ead4ee780756875), após as correções de logs e de limite excessivamente longo. Os quatro casos documentados abaixo passaram, incluindo a ordem dos itens, os campos públicos e os erros HTTP 400.

Também foi confirmado que um `limite` com 4.301 dígitos retorna HTTP 400 com o código `LIMITE_INVALIDO`. Os logs INFO emitiram estratégia, quantidade, duração e status, conforme o RF-08.

Para conferir as versões no ambiente em que o docente reproduzir o mockup:

```bash
python --version
python -m pip show bentoml fastapi
```

## Contrato

`GET /recomendacoes?produtoId=<UUID>&limite=<1..8>` ou `GET /recomendacoes?usuarioId=<UUID>&limite=<1..8>`. Informe **exatamente um** contexto. `limite` é opcional e vale 8 por padrão.

Resposta 200: `{"estrategia":"categoria_regiao_vendas_avaliacao_v1","itens":[...]}`. Cada item contém apenas `id`, `nome`, `preco`, `categoria`, `imagemPrincipal` e `notaMedia`. Erros de entrada retornam HTTP 400 no formato `{"error":{"code":"...","message":"...","details":{}}}`.

Com `produtoId` encontrado, o serviço filtra itens ativos, com estoque e da mesma categoria; exclui o próprio produto e IDs repetidos. Prioriza a região do artesão do produto de contexto e desempata por vendas decrescentes, nota decrescente e UUID crescente. Para `usuarioId`, produto desconhecido ou categoria sem candidatos, usa popularidade geral. O contexto `usuarioId` é apenas um gatilho de cold start neste mockup; não há autenticação nem personalização.

## RFs da AV1 → implementação

| Requisito | Onde verificar | Situação neste mockup |
|---|---|---|
| RF-01 Contexto válido | `GET /recomendacoes` | Aceita exatamente um UUID de produto ou usuário e limite 1–8. |
| RF-02 Elegibilidade | `service.py:elegiveis` | Exclui inativos, sem estoque, duplicados e o produto de contexto. |
| RF-03 Ordenação relacionada | `service.py:recomendacoes` | Mesma categoria, prioridade regional, vendas, nota e UUID. |
| RF-04 Cold start | `service.py:recomendacoes` | Popularidade geral para usuário ou falta de contexto aproveitável. |
| RF-05 Interface | `GET /recomendacoes` | Devolve `estrategia` e no máximo oito DTOs públicos. |
| RF-06 Adapters do frontend | Contrato HTTP neste README | Adapter do frontend fica fora deste mockup isolado. |
| RF-07 Erros | `GET /recomendacoes` | HTTP 400 com códigos `CONTEXTO_INVALIDO` ou `LIMITE_INVALIDO`. |
| RF-08 Observabilidade | `service.py:registrar` | Loga estratégia, quantidade, duração e status sem dados pessoais. |

**Conferência com a AV1 original:** comparei esta tabela com a seção de requisitos funcionais da especificação da AV1 (versão 1.0, 16/09/2026) e com `requirements.md`, usando acesso de leitura. RF-01 a RF-05, RF-07 e RF-08 correspondem ao contrato descrito; RF-06 prevê adapters no frontend e está identificado acima como fora deste mockup isolado. Os documentos originais do Drive exigem uma conta com permissão de leitura; esta tabela permite conferir o escopo do mockup diretamente no repositório.

Os RNFs de desempenho com 1.000 itens e testes contra PostgreSQL real são metas da integração futura e não são demonstrados por este catálogo em memória. O mockup também não implementa sessão, persistência ou os adapters do frontend.

## Casos de teste copiáveis

Os quatro casos abaixo foram executados e passaram no ambiente de validação registrado acima, após as correções de logs INFO e de limite excessivamente longo. Foram conferidos os códigos HTTP, a estratégia, a ordem dos itens e os campos públicos das respostas de sucesso, além dos códigos de erro das entradas inválidas. Compare a resposta real com os campos mostrados; espaços e ordem das chaves JSON podem variar.

### 1. Produto relacionado: região, nota e elegibilidade

```bash
curl -sS 'http://localhost:3000/recomendacoes?produtoId=00000000-0000-4000-8000-000000000001&limite=3'
```

Resultado esperado (HTTP 200): estratégia `categoria_regiao_vendas_avaliacao_v1`; IDs dos itens nesta ordem: `00000000-0000-4000-8000-000000000003`, `00000000-0000-4000-8000-000000000002`, `00000000-0000-4000-8000-000000000004`. Os produtos 5 (inativo) e 6 (sem estoque) e o produto 1 não aparecem.

### 2. Cold start com usuário

```bash
curl -sS 'http://localhost:3000/recomendacoes?usuarioId=00000000-0000-4000-8000-000000000099&limite=2'
```

Resultado esperado (HTTP 200): estratégia `popularidade_geral_v1`; IDs `00000000-0000-4000-8000-000000000007` e `00000000-0000-4000-8000-000000000004`, nessa ordem. São os dois itens elegíveis com mais vendas.

### 3. Dois contextos inválidos

```bash
curl -i 'http://localhost:3000/recomendacoes?produtoId=00000000-0000-4000-8000-000000000001&usuarioId=00000000-0000-4000-8000-000000000099'
```

Resultado esperado: HTTP 400 e corpo `{"error":{"code":"CONTEXTO_INVALIDO","message":"Informe exatamente um contexto de recomendação.","details":{}}}`.

### 4. Limite fora do contrato

```bash
curl -i 'http://localhost:3000/recomendacoes?produtoId=00000000-0000-4000-8000-000000000001&limite=9'
```

Resultado esperado: HTTP 400 e código `LIMITE_INVALIDO`.

## Referências do trabalho

- [Especificação da AV1](https://drive.google.com/file/d/1lbBPER6xpXVq9lHPlZKDtRiMVHZKAAT0/view)
- [Requisitos](https://drive.google.com/file/d/1aIMPG_Qj_mqCTpK6WkdECas2pMCqzEZX/view)
- [Design](https://drive.google.com/file/d/1SDQ5GDwK_6XM377B6QJoTgSXGcjCYAdr/view)
- [Produto](https://drive.google.com/file/d/1p_Y_C7UoktB2OKV9zfE3EUpcdFNfCnLW/view)
- [Documentação do BentoML: aplicações ASGI](https://docs.bentoml.com/en/latest/build-with-bentoml/asgi.html)
