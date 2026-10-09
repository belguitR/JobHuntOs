# Data model

This is the initial relational model for the multi-user product. Tables are grouped by bounded context for ownership, but PostgreSQL remains one database for now. Relationships between contexts are normal and expected; a context may reference another record by ID, but it does not own or modify that record's rules.

Every product table should use a UUID primary key and have `created_at` and `updated_at` timestamps unless it is an immutable event.

## Shared reference data

### `countries`

Reference list of countries, identified by ISO 3166-1 alpha-2 code.

```text
countries
  id
  iso_code              unique, e.g. FR, DE, NL
  name
```

Countries are not owned by a candidate. A candidate selects target countries through `candidate_target_countries`.

## `identity_access`

### `accounts`

```text
accounts
  id
  email                 unique
  password_hash         nullable when using an external identity provider
  is_email_verified
  created_at
  updated_at
```

### `external_connections`

Stores an account's connection to external providers such as Google. OAuth access and refresh tokens must be encrypted at rest.

```text
external_connections
  id
  account_id            -> accounts.id
  provider              e.g. google
  provider_subject      provider user identifier
  encrypted_tokens
  scopes
  expires_at
  created_at
  updated_at
```

## `candidate`

### `candidate_profiles`

One profile per account.

```text
candidate_profiles
  id
  account_id            -> accounts.id, unique
  given_name
  family_name
  contact_email
  phone                 nullable
  city                  nullable
  country_id            -> countries.id, nullable
  headline              nullable
  created_at
  updated_at
```

### `candidate_languages`

Languages are rows, not a comma-separated field.

```text
candidate_languages
  candidate_id          -> candidate_profiles.id
  language_code          e.g. en, fr, de
  proficiency            e.g. native, fluent, professional, basic
  primary key (candidate_id, language_code)
```

### `candidate_target_countries`

```text
candidate_target_countries
  candidate_id          -> candidate_profiles.id
  country_id            -> countries.id
  priority
  work_authorization    nullable
  notes                 nullable
  primary key (candidate_id, country_id)
```

### `cv_documents` and `cv_versions`

A document is the CV as a whole; versions preserve its history and tailored copies.

```text
cv_documents
  id
  candidate_id          -> candidate_profiles.id
  name
  archived_at           nullable

cv_versions
  id
  cv_document_id        -> cv_documents.id
  parent_version_id     -> cv_versions.id, nullable
  version_number
  language
  target_role           nullable
  storage_key
  filename
  media_type
  sha256
  extracted_text        nullable
  created_at
```

The file itself belongs in object storage, not PostgreSQL. PostgreSQL stores its metadata and storage key. The original upload remains immutable; a tailored CV is a new version.

## `job_propositions`

### `job_sources`

```text
job_sources
  id
  name
  source_type           e.g. greenhouse, lever, company_careers
  base_url
```

### `job_offers`

One canonical record per discovered offer. The job finder provides the source data; this context validates and deduplicates it.

```text
job_offers
  id
  source_id             -> job_sources.id
  external_id           nullable
  fingerprint           unique, used for deduplication
  canonical_url
  application_url
  company_name
  company_website       nullable
  title
  location_text         nullable
  country_id            -> countries.id, nullable
  remote_policy         nullable
  employment_type       nullable
  description_text
  published_at          nullable
  first_seen_at
  last_seen_at
  is_active
```

### `candidate_job_matches` and `candidate_job_decisions`

```text
candidate_job_matches
  candidate_id          -> candidate_profiles.id
  job_offer_id          -> job_offers.id
  score
  reasons               JSONB
  calculated_at
  primary key (candidate_id, job_offer_id)

candidate_job_decisions
  candidate_id          -> candidate_profiles.id
  job_offer_id          -> job_offers.id
  decision              saved | dismissed
  decided_at
  primary key (candidate_id, job_offer_id)
```

## `applications`

### `applications`

`job_offer_id` is optional so that a candidate can add a manually found application. Snapshot fields preserve history when the source offer changes or disappears.

```text
applications
  id
  candidate_id          -> candidate_profiles.id
  job_offer_id          -> job_offers.id, nullable
  cv_version_id         -> cv_versions.id, nullable
  company_name_snapshot
  job_title_snapshot
  job_url_snapshot       nullable
  status
  applied_at             nullable
  notes                  nullable
  created_at
  updated_at
```

### Supporting application records

```text
application_status_events
  id
  application_id        -> applications.id
  from_status           nullable
  to_status
  occurred_at
  note                  nullable

contacts
  id
  candidate_id          -> candidate_profiles.id
  full_name
  email                 nullable
  phone                 nullable
  linkedin_url          nullable

application_contacts
  application_id        -> applications.id
  contact_id            -> contacts.id
  role                  nullable
  primary key (application_id, contact_id)

email_drafts
  id
  application_id        -> applications.id
  recipient_email
  subject
  body
  status                prepared | approved | created_in_gmail | sent
  provider_draft_id     nullable
  approved_at           nullable
  created_at

follow_ups
  id
  application_id        -> applications.id
  contact_id            -> contacts.id, nullable
  due_at
  completed_at          nullable
  note                  nullable

interviews
  id
  application_id        -> applications.id
  scheduled_at
  interview_type        nullable
  meeting_url           nullable
  notes                 nullable
```

## Storage rules

- Store job descriptions as `TEXT` in PostgreSQL. A normal job description is not large enough to justify separate file storage.
- Do not render untrusted source HTML directly. Convert it to safe text or sanitized HTML before displaying it.
- Do not download company images or logos initially. Store an optional external URL only if it is useful; it is not core product data.
- Store user-uploaded CV files in private object storage. Do not put PDF or DOCX binary data in PostgreSQL.
