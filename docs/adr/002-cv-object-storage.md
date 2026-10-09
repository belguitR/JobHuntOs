# ADR 002: CV object storage

**Status:** Accepted  
**Date:** 2026-10-09

## Decision

Store user-uploaded CV files in a private Cloudflare R2 bucket with the `eu` jurisdiction. PostgreSQL stores document metadata and the R2 object key; it does not store PDF or DOCX bytes.

FastAPI is the only component with permanent R2 credentials. After confirming that the authenticated candidate owns a document, it creates short-lived signed upload or download URLs. The bucket is never public.

Object keys are internal identifiers, not user-provided filenames:

```text
cvs/{candidate_id}/{cv_document_id}/{cv_version_id}/{random_uuid}
```

## Context

CVs are private personal documents. Object storage separates file handling from PostgreSQL and keeps the core server portable through R2's S3-compatible API.

Cloudflare R2's current free tier includes 10 GB of storage, 1 million Class A operations, and 10 million Class B operations per month. That is sufficient for the initial small user base, but pricing and limits must be rechecked before relying on them at scale. [R2 pricing](https://developers.cloudflare.com/r2/pricing/)

R2 supports an EU jurisdictional restriction, which guarantees that objects are stored and processed in the European Union. [R2 data location](https://developers.cloudflare.com/r2/reference/data-location/)

## Consequences

- The server needs an R2/S3 adapter and secrets in deployment configuration.
- CV metadata includes the object key, original filename, media type, hash, and size.
- Deleting a CV version must remove its object after database ownership checks.
- The browser never receives permanent storage credentials.
