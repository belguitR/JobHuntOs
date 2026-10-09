import React, { useState } from 'react';
import { request, singular, statuses, today, countryId } from './api';
import { Modal, ErrorBox } from './components';

const field = (key, label, type = 'text', required = false, options = null) => ({
  key,
  label,
  type,
  required,
  options,
});
const priority = field('priority', 'Priority', 'select', true, ['High', 'Medium', 'Low']);
const notes = field('notes', 'Notes', 'textarea');
const url = (key, label) => field(key, label, 'url');
const definitions = {
  countries: [
    field('name', 'Country name', 'text', true),
    field('code', 'Two-letter country code', 'text', true),
    priority,
    field('target_roles', 'Target roles'),
    field('salary_notes', 'Salary target / currency / period'),
    field('visa_notes', 'Visa & work authorization notes', 'textarea'),
    field('language_notes', 'Language notes', 'textarea'),
    field('job_boards', 'Job boards', 'textarea'),
    notes,
  ],
  companies: [
    field('country_id', 'Country', 'country', true),
    field('name', 'Company name', 'text', true),
    url('website', 'Website'),
    field('email', 'Company email', 'email'),
    url('linkedin', 'LinkedIn company URL'),
    field('sponsorship', 'Visa sponsorship', 'select', false, ['Unknown', 'Yes', 'No']),
    notes,
  ],
  contacts: [
    field('country_id', 'Country', 'country', true),
    field('company_id', 'Company', 'company'),
    field('name', 'Full name', 'text', true),
    field('title', 'Job title'),
    field('email', 'Email', 'email'),
    url('linkedin', 'LinkedIn profile URL'),
    field('contact_type', 'Contact type', 'select', false, [
      'Recruiter',
      'Engineer',
      'Manager',
      'Alumni',
      'Founder',
      'Other',
    ]),
    field('relationship', 'Relationship', 'select', false, [
      'Discovered',
      'Connection sent',
      'Connected',
      'Messaged',
      'Replied',
      'Ongoing',
      'Dormant',
    ]),
    notes,
  ],
  applications: [
    field('company_id', 'Company', 'company', true),
    field('title', 'Role title', 'text', true),
    field('status', 'Status', 'select', true, statuses),
    priority,
    field('resume_id', 'Exact CV version', 'resume'),
    field('source', 'Source'),
    url('job_url', 'Job URL'),
    field('location', 'City / remote arrangement'),
    field('salary_notes', 'Salary / currency / period'),
    field('date_applied', 'Applied on', 'date'),
    field('first_response_at', 'First response on', 'date'),
    field('description', 'Job description', 'textarea'),
    notes,
  ],
  followups: [
    field('country_id', 'Country', 'country', true),
    field('title', 'What needs to happen?', 'text', true),
    field('due_date', 'Due date', 'date', true),
    field('application_id', 'Related application', 'application'),
    field('contact_id', 'Related contact', 'contact'),
    notes,
  ],
  interviews: [
    field('application_id', 'Application', 'application', true),
    field('title', 'Interview type / title', 'text', true),
    field('scheduled_at', 'Interview time (your local timezone)', 'datetime-local', true),
    field('duration_minutes', 'Duration in minutes', 'number', true),
    field('interviewer', 'Interviewer'),
    url('meeting_url', 'Meeting link'),
    field('status', 'Status', 'select', true, ['Scheduled', 'Completed', 'Cancelled']),
    field('notes_before', 'Preparation notes', 'textarea'),
    field('notes_after', 'Feedback & questions encountered', 'textarea'),
  ],
  interactions: [
    field('contact_id', 'Contact', 'contact', true),
    field('application_id', 'Related application', 'application'),
    field('kind', 'Interaction type', 'select', true, [
      'Note',
      'LinkedIn message',
      'Email sent',
      'Reply received',
      'Call',
      'Meeting',
    ]),
    field('occurred_at', 'When (your local timezone)', 'datetime-local', true),
    field('content', 'Message / conversation notes', 'textarea', true),
  ],
  resumes: [
    field('name', 'CV name', 'text', true),
    field('language', 'Language'),
    field('target_role', 'Target role'),
    notes,
  ],
};
function localDatetime(value) {
  const date = new Date(value || Date.now());
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
}
export function RecordForm({ kind, record, defaults = {}, data, onClose, onSaved }) {
  const fields = definitions[kind];
  const [values, setValues] = useState(() =>
    Object.fromEntries(
      fields.map((f) => {
        let value =
          record?.[f.key] ??
          defaults[f.key] ??
          (f.key === 'priority'
            ? 'Medium'
            : f.key === 'duration_minutes'
              ? 60
              : f.key === 'due_date'
                ? today()
                : f.type === 'select'
                  ? f.options[0]
                  : '');
        if (f.type === 'datetime-local') value = localDatetime(value || null);
        return [f.key, value];
      }),
    ),
  );
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const selectedCountry = Number(values.country_id || defaults.country_id || 0);
  const selectedCompany = data.companies.find((c) => c.id === Number(values.company_id));
  const scope = selectedCompany?.country_id || selectedCountry;
  function options(f) {
    if (f.type === 'select') return f.options.map((v) => ({ id: v, name: v }));
    if (f.type === 'country') return data.countries;
    const collection = {
      company: 'companies',
      resume: 'resumes',
      application: 'applications',
      contact: 'contacts',
    }[f.type];
    return (data[collection] || [])
      .filter(
        (r) =>
          (!scope || countryId(data, collection, r) === scope) &&
          (f.type !== 'resume' || !r.archived || r.id === record?.resume_id),
      )
      .map((r) => ({
        id: r.id,
        name:
          f.type === 'resume'
            ? `${r.name} · v${r.version}`
            : f.type === 'application'
              ? `${r.title} · ${data.companies.find((c) => c.id === r.company_id)?.name}`
              : r.name,
      }));
  }
  function change(f, value) {
    setValues((v) => {
      const next = { ...v, [f.key]: f.key === 'code' ? value.toUpperCase() : value };
      if (f.key === 'country_id')
        for (const key of ['company_id', 'contact_id', 'application_id', 'resume_id'])
          if (key in next) next[key] = '';
      if (f.key === 'company_id' && 'resume_id' in next) next.resume_id = '';
      return next;
    });
  }
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      const payload = Object.fromEntries(
        fields.map((f) => {
          let value = values[f.key];
          if (f.key.endsWith('_id') || f.type === 'number')
            value = value === '' ? null : Number(value);
          if (f.type === 'date' && !value) value = null;
          if (f.type === 'datetime-local') value = new Date(value).toISOString();
          return [f.key, value];
        }),
      );
      const result = await request(`/${kind}${record ? `/${record.id}` : ''}`, {
        method: record ? 'PATCH' : 'POST',
        body: JSON.stringify(payload),
      });
      await onSaved(result);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title={`${record ? 'Edit' : 'Add'} ${singular[kind]}`} onClose={onClose}>
      <form onSubmit={submit}>
        <ErrorBox error={error} />
        <div className="form-grid">
          {fields.map((f) => (
            <label className={f.type === 'textarea' ? 'span-two' : ''} key={f.key}>
              {f.label}
              {f.required && <span aria-hidden="true"> *</span>}
              {['select', 'country', 'company', 'resume', 'application', 'contact'].includes(
                f.type,
              ) ? (
                <select
                  value={values[f.key]}
                  required={f.required}
                  disabled={Boolean(
                    record &&
                    (f.key === 'country_id' || (f.key === 'company_id' && kind === 'applications')),
                  )}
                  onChange={(e) => change(f, e.target.value)}
                >
                  <option value="" disabled={f.type === 'select'}>
                    {f.required ? `Choose ${f.label.toLowerCase()}` : 'None'}
                  </option>
                  {options(f).map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name}
                    </option>
                  ))}
                </select>
              ) : f.type === 'textarea' ? (
                <textarea
                  rows="4"
                  required={f.required}
                  value={values[f.key]}
                  onChange={(e) => change(f, e.target.value)}
                />
              ) : (
                <input
                  type={f.type}
                  required={f.required}
                  value={values[f.key]}
                  onChange={(e) => change(f, e.target.value)}
                  maxLength={f.key === 'code' ? 2 : undefined}
                  min={f.type === 'number' ? 5 : undefined}
                  max={f.type === 'number' ? 720 : undefined}
                />
              )}
            </label>
          ))}
        </div>
        <div className="form-footer">
          <button type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function UploadForm({ data, country, onSaved, onClose }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(e) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setBusy(true);
    setError('');
    try {
      await request('/resumes/upload', { method: 'POST', body: form });
      await onSaved();
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title="Upload a CV" onClose={onClose}>
      <form onSubmit={submit}>
        <ErrorBox error={error} />
        <p className="muted">Your original file is stored locally. PDF and DOCX, up to 15 MB.</p>
        <label>
          Country
          <select name="country_id" required defaultValue={country || ''}>
            <option value="">Choose country</option>
            {data.countries.map((c) => (
              <option value={c.id} key={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          CV name
          <input name="name" required maxLength="200" placeholder="e.g. Japan · Backend" />
        </label>
        <div className="form-grid">
          <label>
            Language
            <input name="language" />
          </label>
          <label>
            Target role
            <input name="target_role" />
          </label>
        </div>
        <label>
          File
          <input name="file" type="file" accept=".pdf,.docx" required />
        </label>
        <div className="form-footer">
          <button type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={busy}>
            {busy ? 'Uploading…' : 'Upload CV'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
