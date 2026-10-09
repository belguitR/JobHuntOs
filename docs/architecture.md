# Job Hunt OS architecture

The country is the root of the user's job-search organization. Companies, contacts and CVs have an explicit country foreign key. Applications belong to a company, and inherit that company's country. A company can appear separately in multiple countries, with different local contacts and applications. Contacts may be independent or belong to one company in their country.

Applications reference exact CV file versions. Uploads use generated storage names and SHA-256 hashes. DOCX edits create new files and version records with parent links. The editor replaces only XML text nodes, preserving the other document parts; changing text length can still change pagination in Word. PDF preview/download is supported; direct PDF text editing is not.

SQLite foreign keys prevent orphaned records. Validation rejects cross-country links. Status updates and their history entries commit together. Generic routing is limited to an explicit model/table allowlist. Each input schema rejects unknown fields; SQL values use bound parameters. Linked records prevent deletion, with an actionable conflict message. CVs are archived rather than deleted.

The React client has separate API, shared components, forms, record lists, detail pages, dashboard, analytics and document editor modules. It reads its workspace from the API; dashboard numbers and analytics are derived from those records. Hash routes make individual records linkable. Country filtering applies to lists, dashboard, analytics and global search. The app refreshes on focus and every 15 seconds while visible, including extension-created records.

Backend modules separate schema contracts, storage, business validation and document handling from HTTP routes. The database starts empty. Schema version 1 is created automatically in app/database.py. Future structural changes must introduce a migration rather than replacing saved tables. The old prototype's jobhunt.db is preserved; it had zero application records when the replacement was made.

The extension uses Manifest V3 and the local API. Manual capture is user-triggered with activeTab. Optional success-page hints are restricted to Greenhouse and Lever and require user permission. A hint is a proposal, not proof of submission, and needs confirmation. The browser extension must be installed by loading its folder in the browser.

Local operation requires no paid services, account, Redis, or authentication. Reminders are stored due dates shown in the app; there are no email or push notifications. The servers bind to loopback by default. This is a single-person local workspace, not a publicly deployable multi-user service.

Backup: stop the API and copy backend/data (database plus uploads). The web export downloads records as JSON; it does not include CV files and is not a complete backup.
