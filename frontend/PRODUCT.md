# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

The primary user is an individual managing an international job search across several countries. They need one reliable place to organize active opportunities, people, documents, deadlines, and country-specific constraints while applying from a desktop browser and checking essential work on mobile.

## Product Purpose

Job Hunt OS turns a fragmented international job search into a connected operational workspace. Success means the user can see what needs attention, preserve the exact context of every application, and move between countries without losing company, contact, CV, interview, or follow-up relationships.

## Positioning

The product is organized around countries as first-class workspaces rather than treating country as a tag on an application. Each country aggregates its companies, contacts, CV versions, applications, interviews, follow-ups, visa notes, language requirements, salary targets, and job-board sources.

## Operating Context

Users research roles in a browser, save companies and public professional contacts, upload and tailor CVs, submit applications, prepare for interviews, record conversations, and schedule follow-ups. A lightweight browser extension can capture the current job or contact page into the local workspace after user review. The dashboard and every collection can be scoped to one country or all countries.

## Capabilities and Constraints

- Countries contain country-specific strategy and aggregate related records.
- Every company belongs to one country; applications belong to companies.
- Contacts belong to a country and may belong to a company or application interaction.
- CVs belong to a country. PDF and DOCX uploads are stored locally, and DOCX text edits create immutable new versions while existing applications keep their original version.
- Applications track priority, source, status, dates, role details, job description, exact CV version, and status history.
- Interviews belong to applications. Follow-ups belong to a country and may reference an application or contact.
- Application collections support table and Kanban views, filtering, and drag-to-change status.
- Analytics derive from real saved applications, responses, interviews, offers, countries, CVs, and sources.
- Global and section-level search operate within the active country scope.
- Data can be exported as JSON.
- The current stack is React, FastAPI, SQLite, and local filesystem storage.
- Authentication, cloud sync, collaboration, and unattended application submission are not currently included.
- The browser extension does not silently save records or collect general browsing history; the user reviews captured data before saving.

## Brand Commitments

The product name is Job Hunt OS. Interface language is direct, concise, and operational. It must not use motivational slogans, generic productivity phrases, fake social proof, or invented claims. The spelling “company” is required for the singular entity.

## Evidence on Hand

The repository contains a working React frontend, FastAPI API, SQLite schema, local CV storage and editing, browser extension, responsive styles, existing user data, and automated backend tests. There are no testimonials, customer logos, commercial benchmarks, or other marketing claims to present.

## Product Principles

- Countries are workspaces, not filters.
- Relationships between records must remain visible and intact.
- Operational clarity takes precedence over decorative novelty.
- Distinctive moments should explain place, state, or cause.
- User data remains reviewable, exportable, and locally controlled.

## Accessibility & Inclusion

The interface must support keyboard focus, reduced-motion preferences, readable contrast, responsive layouts, and explicit labels for icon-only controls.
