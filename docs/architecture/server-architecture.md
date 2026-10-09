# Server architecture

The core server is a FastAPI modular monolith designed with Domain-Driven Design and hexagonal architecture. It contains four bounded contexts. They are modules inside one server for now, but their boundaries should allow a context to be extracted later if there is a real operational reason to do so. The objective is clear ownership and low coupling, not microservices by default.

- `identity_access` — accounts, authentication, authorization, and Google connection management.
- `candidate` — profile, verified facts, search preferences, target countries, CVs, and CV versions.
- `applications` — application pipeline, contacts, follow-ups, and approved Gmail draft actions.
- `job_propositions` — collected job offers, source links, matching, and a candidate's saved or dismissed offers.

The separate Python `job_finder` is not part of the core server. It is a worker that finds and normalizes public offers, then submits them to `job_propositions` through a narrow internal contract.

## Shape of the server

```text
React client
    |
    v
FastAPI
  middleware: request ID, authentication, rate limiting, error handling
    |
    +-- identity_access
    +-- candidate
    +-- applications ----> Gmail adapter ----> Gmail API
    +-- job_propositions <---- job_finder worker
    |
    +-- PostgreSQL (source of truth)
    +-- Redis (cache and short-lived operational data)
```

Authentication middleware validates the session/JWT and makes the current identity available to the request. Each use case still performs its own authorization checks; a valid token alone does not grant access to another candidate's data.

## Internal structure of each context

```text
HTTP router / request-response schemas        inbound adapter
                |
                v
use cases / application services              orchestrate one business action
                |
                v
domain                                        entities, value objects, domain rules
                |
                v
ports                                         repository and external-service interfaces
                |
                v
infrastructure adapters                       PostgreSQL/ORM, Redis, Gmail, HTTP clients
```

The domain is pure Python: no FastAPI, ORM, Redis, or Gmail imports. ORM models and repository implementations live in infrastructure. A context owns its own repository interfaces and business rules, even though every repository initially uses the same PostgreSQL instance.

Routers are documented through FastAPI's OpenAPI/Swagger interface. Request and response schemas are explicit and separate from domain objects. API naming conventions should be chosen once and applied consistently; the current preference is `snake_case`.

## Data and external integrations

- PostgreSQL is the source of truth. Redis never becomes the only copy of business data.
- Redis uses cache-aside only where it helps. Not every query needs caching; cache keys, TTLs, and invalidation are decided per use case.
- Gmail is an outbound adapter owned by `applications`, not a separate service. Draft creation and sending require an explicit user-approved action.
- The job finder does not write directly to application data. `job_propositions` validates, deduplicates, and stores canonical offers.

## Quality baseline

- Unit tests for domain rules and use cases.
- Integration tests for repositories, database migrations, and external adapters.
- Clear dependency direction: adapters depend on ports; the domain does not depend on frameworks.
- Small, focused modules and explicit contracts between contexts.
