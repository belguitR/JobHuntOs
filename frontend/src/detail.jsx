import React, { useState } from 'react';
import { countryId, dateLabel, displayName, flag, statuses } from './api';
import { Badge, External, Section } from './components';
import { Records } from './records';

export function Detail({
  kind,
  record: r,
  data,
  open,
  add,
  edit,
  remove,
  update,
  editCV,
  selectCountry,
}) {
  const [tab, setTab] = useState('Overview');
  const country = data.countries.find((c) => c.id === countryId(data, kind, r));
  const company = data.companies.find((c) => c.id === r.company_id);
  const application = data.applications.find((a) => a.id === r.application_id);
  const cv = data.resumes.find((c) => c.id === r.resume_id);
  const tabs =
    kind === 'countries'
      ? ['Overview', 'Companies', 'CVs', 'Contacts', 'Applications', 'Follow-ups']
      : kind === 'companies'
        ? ['Overview', 'Applications', 'Contacts']
        : kind === 'applications'
          ? ['Overview', 'Timeline', 'Contacts', 'Interviews', 'Follow-ups']
          : kind === 'contacts'
            ? ['Overview', 'Conversations', 'Follow-ups']
            : ['Overview'];
  function related(collection) {
    return data[collection].filter((x) =>
      kind === 'countries'
        ? countryId(data, collection, x) === r.id
        : kind === 'companies'
          ? x.company_id === r.id
          : kind === 'applications'
            ? collection === 'contacts'
              ? x.company_id === r.company_id
              : x.application_id === r.id
            : x.contact_id === r.id,
    );
  }
  const defaults =
    kind === 'countries'
      ? { country_id: r.id }
      : kind === 'companies'
        ? { country_id: r.country_id, company_id: r.id }
        : kind === 'applications'
          ? { country_id: country?.id, company_id: r.company_id, application_id: r.id }
          : { country_id: country?.id, company_id: r.company_id, contact_id: r.id };
  const relatedKind = {
    Companies: 'companies',
    CVs: 'resumes',
    Contacts: 'contacts',
    Applications: 'applications',
    Interviews: 'interviews',
    'Follow-ups': 'followups',
  }[tab];
  const displayed = Object.entries(r).filter(
    ([k, v]) =>
      ![
        'id',
        'country_id',
        'company_id',
        'resume_id',
        'application_id',
        'contact_id',
        'created_at',
        'updated_at',
        'sha256',
        'parent_id',
        'filename',
        'mime',
        'version',
        'archived',
      ].includes(k) &&
      v !== '' &&
      v !== null &&
      !['name', 'title', 'status', 'completed'].includes(k),
  );
  const fieldLabels = {
    code: 'Country code',
    target_roles: 'Target roles',
    visa_notes: 'Visa & work authorization',
    language_notes: 'Language',
    salary_notes: 'Salary expectations',
    job_boards: 'Job boards',
    target_role: 'Target role',
    date_applied: 'Applied on',
    first_response_at: 'First response',
    contact_type: 'Contact type',
    due_date: 'Due date',
    scheduled_at: 'Scheduled time',
    notes_before: 'Preparation',
    notes_after: 'Feedback',
    duration_minutes: 'Duration (minutes)',
    job_url: 'Job link',
    meeting_url: 'Meeting link',
  };
  return (
    <div className="detail-page">
      <div className="breadcrumbs">
        {country && (
          <button onClick={() => open('countries', country.id)}>
            {flag(country.code)} {country.name}
          </button>
        )}
        {company && (
          <>
            <span>/</span>
            <button onClick={() => open('companies', company.id)}>{company.name}</button>
          </>
        )}
        <span>/</span>
        <span>{displayName(kind, r)}</span>
      </div>
      <div className="entity-header">
        <div>
          <span className="eyebrow">
            {kind === 'countries'
              ? 'COUNTRY WORKSPACE'
              : kind === 'companies'
                ? 'COMPANY'
                : kind === 'resumes'
                  ? `CV VERSION ${r.version}`
                  : kind.toUpperCase()}
          </span>
          <h1>{displayName(kind, r)}</h1>
          <p>
            {kind === 'countries'
              ? 'Companies, contacts, CVs and applications for this country.'
              : company?.name || country?.name || ''}
          </p>
        </div>
        <div className="entity-actions">
          {kind === 'countries' && (
            <button onClick={() => selectCountry(r.id)}>Use as country filter</button>
          )}
          <button onClick={() => edit(kind, r)}>Edit {kind === 'resumes' ? 'details' : ''}</button>
          {kind !== 'resumes' && (
            <button className="danger-text" onClick={() => remove(kind, r)}>
              Delete
            </button>
          )}
          {kind === 'companies' && (
            <button className="primary" onClick={() => add('applications', defaults)}>
              ＋ Application
            </button>
          )}
          {kind === 'countries' && (
            <button className="primary" onClick={() => add('companies', defaults)}>
              ＋ Company
            </button>
          )}
          {kind === 'contacts' && (
            <button className="primary" onClick={() => add('interactions', defaults)}>
              ＋ Conversation
            </button>
          )}
        </div>
      </div>
      <div className="tabs" role="tablist">
        {tabs.map((t) => (
          <button
            role="tab"
            aria-selected={tab === t}
            className={tab === t ? 'active' : ''}
            key={t}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {relatedKind ? (
        <>
          <div className="section-heading">
            <h2>{tab}</h2>
            <button className="primary" onClick={() => add(relatedKind, defaults)}>
              ＋ Add{' '}
              {relatedKind === 'companies'
                ? 'company'
                : relatedKind === 'resumes'
                  ? 'CV'
                  : relatedKind === 'contacts'
                    ? 'contact'
                    : relatedKind === 'applications'
                      ? 'application'
                      : relatedKind === 'interviews'
                        ? 'interview'
                        : 'follow-up'}
            </button>
          </div>
          <Records
            key={relatedKind}
            kind={relatedKind}
            rows={related(relatedKind)}
            data={data}
            open={open}
            add={(k) => add(k, defaults)}
            update={update}
          />
        </>
      ) : tab === 'Timeline' ? (
        <Section title="Status history">
          <div className="timeline">
            {data.status_history
              .filter((h) => h.application_id === r.id)
              .map((h) => (
                <div key={h.id}>
                  <i />
                  <time>{new Date(h.changed_at).toLocaleString()}</time>
                  <b>
                    {h.previous_status ? `${h.previous_status} → ` : 'Created as '}
                    {h.new_status}
                  </b>
                </div>
              ))}
          </div>
        </Section>
      ) : tab === 'Conversations' ? (
        <Section
          title="Conversation history"
          action={
            <button onClick={() => add('interactions', defaults)}>＋ Record interaction</button>
          }
        >
          {data.interactions
            .filter((i) => i.contact_id === r.id)
            .map((i) => (
              <article className="conversation" key={i.id}>
                <div>
                  <Badge>{i.kind}</Badge>
                  <small>{new Date(i.occurred_at).toLocaleString()}</small>
                  <button className="text-button" onClick={() => edit('interactions', i)}>
                    Edit
                  </button>
                  <button
                    className="text-button danger-text"
                    onClick={() => remove('interactions', i)}
                  >
                    Delete
                  </button>
                </div>
                <p>{i.content}</p>
                {i.application_id && (
                  <button
                    className="text-button"
                    onClick={() => open('applications', i.application_id)}
                  >
                    Open linked application →
                  </button>
                )}
              </article>
            ))}
          {!data.interactions.some((i) => i.contact_id === r.id) && (
            <p className="quiet-state">
              Record messages and replies here. A reply linked to an application records its first
              response date.
            </p>
          )}
        </Section>
      ) : (
        <div className="detail-grid">
          <Section title="Overview">
            {kind === 'applications' && (
              <label>
                Current stage
                <select
                  value={r.status}
                  onChange={(e) => update(kind, r.id, { status: e.target.value })}
                >
                  {statuses.map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
            )}
            {kind === 'followups' && (
              <button
                className={r.completed ? '' : 'primary'}
                onClick={() => update(kind, r.id, { completed: !r.completed })}
              >
                {r.completed ? 'Reopen follow-up' : '✓ Mark complete'}
              </button>
            )}
            {kind === 'interviews' && (
              <label>
                Status
                <select
                  value={r.status}
                  onChange={(e) => update(kind, r.id, { status: e.target.value })}
                >
                  {['Scheduled', 'Completed', 'Cancelled'].map((s) => (
                    <option key={s}>{s}</option>
                  ))}
                </select>
              </label>
            )}
            <dl className="details">
              {displayed.map(([k, v]) => (
                <React.Fragment key={k}>
                  <dt>
                    {fieldLabels[k] || k.replaceAll('_', ' ').replace(/^./, (c) => c.toUpperCase())}
                  </dt>
                  <dd>
                    {['website', 'linkedin', 'job_url', 'meeting_url'].includes(k) ? (
                      <External url={v} />
                    ) : k === 'email' ? (
                      <a href={`mailto:${v}`}>{v}</a>
                    ) : k === 'scheduled_at' ? (
                      new Date(v).toLocaleString()
                    ) : ['date_applied', 'first_response_at', 'due_date'].includes(k) ? (
                      dateLabel(v)
                    ) : (
                      String(v)
                    )}
                  </dd>
                </React.Fragment>
              ))}
            </dl>
            {!displayed.length && (
              <p className="quiet-state">Edit this record to add more details.</p>
            )}
          </Section>
          <div className="detail-side">
            {kind === 'countries' && (
              <Section title="In this country">
                <div className="mini-metrics">
                  {[
                    ['Companies', 'companies'],
                    ['CVs', 'resumes'],
                    ['Contacts', 'contacts'],
                    ['Applications', 'applications'],
                  ].map(([label, key]) => (
                    <button key={key} onClick={() => setTab(label)}>
                      <strong>{related(key).length}</strong>
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              </Section>
            )}
            {kind === 'companies' && (
              <Section title="Company connections">
                <button className="record-row" onClick={() => setTab('Applications')}>
                  Applications <b>{related('applications').length}</b>
                </button>
                <button className="record-row" onClick={() => setTab('Contacts')}>
                  Contacts <b>{related('contacts').length}</b>
                </button>
                <button onClick={() => add('contacts', defaults)}>＋ Add contact</button>
              </Section>
            )}
            {kind === 'applications' && (
              <>
                <Section title="CV used">
                  {cv ? (
                    <button className="row-link" onClick={() => open('resumes', cv.id)}>
                      <b>
                        {cv.name} · v{cv.version}
                      </b>
                      <small>Exact file attached to this application</small>
                    </button>
                  ) : (
                    <p className="quiet-state">
                      No CV selected. Edit this application to attach one.
                    </p>
                  )}
                </Section>
                <Section title="Next action">
                  <button onClick={() => add('followups', defaults)}>＋ Schedule follow-up</button>
                  <button onClick={() => add('interviews', defaults)}>＋ Add interview</button>
                </Section>
              </>
            )}
            {kind === 'resumes' && (
              <>
                <Section title="Document">
                  <p>{r.filename}</p>
                  <div className="stack">
                    <a className="button primary" href={`/api/resumes/${r.id}/file`}>
                      Download CV
                    </a>
                    {r.mime === 'application/pdf' ? (
                      <a
                        className="button"
                        href={`/api/resumes/${r.id}/file?preview=true`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Preview PDF ↗
                      </a>
                    ) : (
                      <button onClick={() => editCV(r)}>Edit text → save new version</button>
                    )}
                    <button onClick={() => update('resumes', r.id, { archived: !r.archived })}>
                      {r.archived ? 'Restore to active CVs' : 'Archive CV'}
                    </button>
                  </div>
                  <p className="caption">
                    File contents are preserved for existing applications. Archive hides this CV
                    from new application choices.
                  </p>
                  {r.parent_id && (
                    <button className="text-button" onClick={() => open('resumes', r.parent_id)}>
                      Open parent version →
                    </button>
                  )}
                </Section>
                <Section title="Used by applications">
                  {data.applications
                    .filter((a) => a.resume_id === r.id)
                    .map((a) => (
                      <button
                        className="record-row"
                        key={a.id}
                        onClick={() => open('applications', a.id)}
                      >
                        {a.title}
                        <Badge>{a.status}</Badge>
                      </button>
                    ))}
                  {!data.applications.some((a) => a.resume_id === r.id) && (
                    <p className="quiet-state">Not attached to an application yet.</p>
                  )}
                </Section>
              </>
            )}
            {application && (
              <Section title="Linked application">
                <button className="row-link" onClick={() => open('applications', application.id)}>
                  {application.title} →
                </button>
              </Section>
            )}
            {r.contact_id && (
              <Section title="Linked contact">
                <button className="row-link" onClick={() => open('contacts', r.contact_id)}>
                  {data.contacts.find((c) => c.id === r.contact_id)?.name} →
                </button>
              </Section>
            )}
            <Section title="Record details">
              <p className="caption">
                Added {dateLabel(r.created_at)}
                <br />
                Updated {dateLabel(r.updated_at)}
              </p>
            </Section>
          </div>
        </div>
      )}
    </div>
  );
}
