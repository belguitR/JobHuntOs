# ADR 003: Job Finder worker

**Status:** Accepted  
**Date:** 2026-10-10

## Decision

Run job collection as a separate Python worker. It is an ingestion pipeline, not a domain-heavy service and does not use full DDD or hexagonal layering.

Each enabled source is collected once per hour. A source cannot have two concurrent runs. Failed sources retry with backoff before returning to the normal hourly cadence.

```text
source adapter
    -> OfferFactory
    -> validated, normalized offer
    -> within-run deduplication
    -> durable delivery outbox
    -> private Job Discovery ingestion endpoint
```

The worker owns source configuration, run history, source checkpoints, and its delivery outbox. It does not own canonical job offers, candidate matching, saved/dismissed decisions, or applications. `job_propositions` owns those rules and persists accepted offers.

## Structure

```text
job_finder/
  scheduler/             decides which source is due
  sources/               provider-specific fetch adapters
  offer_intake/          OfferFactory, validation, fingerprints, batch deduplication
  storage/               source state, run history, delivery outbox
  delivery/              Job Discovery ingestion client
  main.py
```

`OfferFactory` converts a provider-specific payload into one `DiscoveredOffer` shape. It normalizes fields, validates required data, and generates a stable source key/fingerprint. It does not access the database or call FastAPI.

Within-run deduplication only removes duplicates returned by a source in the same collection. Canonical cross-run and cross-source deduplication belongs to `job_propositions`.

## Reliability

Collected offers are written to the worker's outbox before delivery. If Job Discovery is unavailable or the worker restarts, pending items are retried rather than lost. Delivery is at-least-once and includes an idempotency key; Job Discovery must treat repeat delivery as safe.

## Consequences

- Job Finder can be deployed and restarted independently of FastAPI.
- The initial integration is a private HTTP batch-ingestion endpoint; no message queue is required yet.
- Redis may provide source locks and rate limiting when more than one worker instance runs. It is not the source of truth.
