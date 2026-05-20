# Threat model — Northwind RAG lab

Project 1 of the ai-sec-rag-lab. Multi-tenant retrieval-augmented chatbot
over a synthetic corporate document corpus. This threat model exists to
make the system's attack surface explicit before we begin testing it,
and to give us a checklist of attacks and mitigations to work through.

## 1. System description

A command-line chatbot that answers questions over a synthetic corpus
("Northwind Robotics" internal documents). Two tenants: `engineering`
and `hr`. Public IT and HR-adjacent documents are visible to both
tenants. HR-confidential documents (salary bands, severance schedule,
PIP procedure, investigations procedure) are visible only to `hr`.

### Components

- **Client**: terminal, invoking `chat()` with `(tenant_id, user_query)`.
- **Application code** (`src/rag/`):
  - `config.py` — env loading and secret redaction
  - `embed.py` — local sentence-transformers model
  - `db.py` — Postgres connection and schema
  - `ingest.py` — chunk corpus files and load into the documents table
  - `retrieve.py` — vector similarity search with SQL-level tenant filter
  - `chat.py` — prompt assembly and Anthropic API call
- **External**: Anthropic API (chat completion), Hugging Face hub
  (one-time model download, then local cache).
- **Data store**: Postgres with pgvector, running in Docker locally.

### Trust boundaries

1. **User input → application**: the `user_query` parameter is fully
   attacker-controlled untrusted data.
2. **Application → Anthropic API**: data leaves the local process over
   a TLS connection to a third party. What we send is what the model
   sees; we have no control over how the model interprets it.
3. **Document corpus → ingestion pipeline**: in Project 1 the corpus
   is author-controlled. Project 2 will model an attacker who can
   write into the corpus.
4. **Application → Postgres**: SQL crosses a network boundary inside
   Docker. The database trusts the application's claimed `tenant_id`
   because there is no DB-level user separation.
5. **Application → external model weights**: in our case the
   sentence-transformers weights come from Hugging Face. A compromised
   model registry could supply backdoored embeddings.

### Security-relevant design decisions

- Tenant filtering is enforced at the SQL `WHERE` clause, never in
  application code after retrieval.
- All SQL is parameterised. No string concatenation builds queries.
- Secrets are loaded from `.env`, gitignored, and redacted in `__repr__`.
- The system prompt is passed via the API's `system` parameter, never
  mixed with user input in the user message.
- Retrieved chunk content is placed in the user message, not the
  system parameter — preventing retrieved data from being elevated
  to instruction-level authority.
- The model is instructed to cite sources and to refuse questions
  outside the provided context.
- No agent capabilities, no tool use, no internet access from the LLM.
  The model has no way to act on the world beyond returning text.

## 2. Threats — STRIDE applied

Each threat below is named, mapped to OWASP LLM Top 10 (2025) and
MITRE ATLAS where applicable, and tagged with whether we will test
for it in this project's break phase.

### Spoofing

**S1. Tenant identity spoofing in the CLI.**
The `tenant_id` parameter is trusted on input — any caller can claim
any tenant. In a real product this would be authenticated; in our lab
the caller is the developer. Out of scope for Project 1 but worth
naming explicitly.

### Tampering

**T1. SQL injection via tenant_id or user_query.**
*OWASP LLM05 (improper output handling, related).*
The application uses parameterised SQL throughout. Tested by attempting
classic injection payloads as tenant_id. Expected outcome: blocked at
the psycopg layer; no SQL syntax interpretation possible.

**T2. Corpus poisoning by adding malicious documents.**
*OWASP LLM03 (supply chain / training data poisoning),
ATLAS AML.T0020.*
Project 2 scope. Noted here for completeness.

**T3. Indirect prompt injection via retrieved chunks.**
*OWASP LLM01 (prompt injection), ATLAS AML.T0051.001.*
A document containing hidden instructions, once retrieved, becomes
part of the prompt and influences the model's output. The model has
no way to distinguish data from instructions inside the user message.
**Will test.**

### Repudiation

**R1. No audit log of queries.**
There is no record of who asked what, when, or what was retrieved.
This is a real gap that would matter in any production deployment
and that Project 4 will address as a detection-engineering exercise.
Noted now so we don't pretend the system has accountability it lacks.

### Information disclosure

**I1. Direct prompt injection to extract the system prompt.**
*OWASP LLM07 (system prompt leakage).*
Despite the system prompt's "do not reveal" directive, well-crafted
queries can extract its contents or paraphrases of it. **Will test.**

**I2. Tenant isolation bypass at the LLM layer.**
*OWASP LLM02 (sensitive information disclosure).*
Retrieval is tenant-filtered, so confidential chunks never enter the
prompt for the wrong tenant. The question is whether the model can
be coaxed into inferring or guessing confidential information from
adjacent public documents plus its own pretraining knowledge.
**Will test.**

**I3. Direct injection to override answer formatting.**
*OWASP LLM01.*
Queries that instruct the model to return data in unusual formats
(e.g. base64, prefixed with the system prompt) test whether output
behaviour can be manipulated beyond simple content. **Will test.**

**I4. Retrieved content disclosure through citation behaviour.**
*OWASP LLM02.*
The model is instructed to cite source filenames. Filenames may
themselves be sensitive (e.g. `hr-pip-procedure.md` reveals that a
PIP procedure exists). **Will test.**

**I5. API key disclosure in logs or output.**
The redacted `__repr__` on `Config` mitigates accidental leaks via
print or exception traceback. Direct attacks via the LLM cannot
recover the key because the key is never placed in any prompt.

### Denial of service

**D1. Resource exhaustion via large queries.**
A query containing tens of thousands of characters could inflate
the prompt and incur high API costs. Not exercised in Project 1;
relevant for production deployment.

**D2. Embedding pipeline starvation during ingest.**
The ingestion path holds open one DB connection while embedding
runs. Not a security threat at our scale; named for completeness.

### Elevation of privilege

**E1. Engineering tenant retrieving HR chunks via SQL bypass.**
The tenant filter is in a `WHERE` clause; bypassing it requires
modifying the application code. No external attack path. Tested
by SQL-injection attempts under T1.

**E2. Engineering tenant retrieving HR information via LLM
inference.**
Same threat as I2 above, listed here under privilege because the
effect is "the engineering caller gains access to information they
should not have."

## 3. What we will test in the break phase

Ordered roughly by difficulty and instructive value:

1. **I1 — System prompt extraction.** Confirms the limits of prompt-
   level directives. Quick to demonstrate, foundational lesson.
2. **I3 — Direct prompt injection on output behaviour.** Tests
   whether the model respects the "answer from context only" rule
   under adversarial framing.
3. **I2 / E2 — Tenant isolation bypass via inference.** The most
   subtle attack of Project 1. Tests whether the model leaks
   information it does not have direct access to.
4. **I4 — Citation-based metadata leakage.** Small but real.
5. **T1 — SQL injection.** Expected to be cleanly blocked, but we
   verify rather than assume.

T3 (indirect prompt injection) is intentionally deferred to Project 2,
where the threat model centres on attacker-controlled documents.

## 4. Mitigations to be tested in the defend phase

For each successful attack, the defend phase will implement and
test at least one mitigation. Likely candidates:

- **Output filtering**: a second-pass LLM-as-judge call to inspect
  the response before returning it.
- **Input filtering**: pattern detection on user queries for known
  injection payloads.
- **Retrieval-time scoring**: refuse to return retrieval results
  when similarity is below a threshold (defends against tenant-
  isolation inference by surfacing "no good answer" cases).
- **Postgres row-level security**: defence-in-depth at the database
  layer, so an application bug cannot leak across tenants.
- **Citation-side filtering**: strip filename hints from responses
  when they would reveal document existence.

Each mitigation will be measured against the attacks it claims to
defend against. A defence that catches an attack 60% of the time
is a defence that fails 40% of the time, and we will report numbers
honestly.

## 5. Out of scope for Project 1

- Authentication and session management (`tenant_id` is trusted input).
- Authorisation beyond per-document tenant ownership.
- Supply chain attacks on the embedding model or its dependencies.
- Adversarial attacks on the embedding model itself (e.g.
  embedding-space poisoning, similarity-score manipulation).
- Network-level attacks on the Anthropic API or its TLS.
- Side channels (timing, cache, model fingerprinting).
- Multi-step attacks combining multiple primitives.
- Any attack requiring write access to the corpus (deferred to
  Project 2).

## 6. Validation

This threat model will be considered validated when:

- Each "Will test" threat has been exercised with at least 5 trials
  to account for LLM output variance.
- Each successful attack has a documented mitigation attempt with
  measured residual risk.
- The repository contains reproducible scripts for every attack
  and defence, runnable by an independent reviewer.
