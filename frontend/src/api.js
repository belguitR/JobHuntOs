export async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers:
      options.body instanceof FormData
        ? options.headers
        : { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    throw new Error(
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((x) => x.msg).join('; ')
          : `Request failed (${response.status})`,
    );
  }
  return response.status === 204 ? null : response.json();
}

export const statuses = [
  'Saved',
  'Contacted',
  'Applied',
  'Screening',
  'Assessment',
  'Technical interview',
  'Final interview',
  'Offer',
  'Accepted',
  'Rejected',
  'Withdrawn',
  'Ghosted',
];
export const terminal = ['Accepted', 'Rejected', 'Withdrawn', 'Ghosted'];
export const singular = {
  countries: 'country',
  companies: 'company',
  contacts: 'contact',
  applications: 'application',
  resumes: 'CV',
  interviews: 'interview',
  followups: 'follow-up',
  interactions: 'interaction',
};
export const labels = {
  countries: 'Countries',
  companies: 'Companies',
  contacts: 'Contacts',
  applications: 'Applications',
  resumes: 'CV library',
  interviews: 'Interviews',
  followups: 'Follow-ups',
};
export const dateLabel = (value) =>
  value
    ? new Date(value.length === 10 ? `${value}T12:00:00` : value).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '—';
export const today = () => {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
};
export const flag = (code) =>
  /^[A-Z]{2}$/.test(code || '')
    ? String.fromCodePoint(...[...code].map((x) => x.charCodeAt(0) + 127397))
    : '◎';
export function countryId(data, kind, row) {
  if (kind === 'countries') return row.id;
  if (row.country_id) return row.country_id;
  if (kind === 'applications')
    return data.companies.find((x) => x.id === row.company_id)?.country_id;
  if (row.application_id)
    return countryId(
      data,
      'applications',
      data.applications.find((x) => x.id === row.application_id) || {},
    );
  if (row.contact_id) return data.contacts.find((x) => x.id === row.contact_id)?.country_id;
  return null;
}
export function displayName(kind, row) {
  return row.name || row.title || row.content || singular[kind];
}
export function stats(data, apps) {
  const submitted = apps.filter((x) => x.date_applied);
  const replied = submitted.filter((x) => x.first_response_at);
  const interviewed = submitted.filter((x) =>
    data.interviews.some((i) => i.application_id === x.id && i.status !== 'Cancelled'),
  );
  const offered = submitted.filter((x) =>
    data.status_history.some(
      (h) => h.application_id === x.id && ['Offer', 'Accepted'].includes(h.new_status),
    ),
  );
  return {
    submitted: submitted.length,
    replied: replied.length,
    interviewed: interviewed.length,
    offered: offered.length,
    rate: submitted.length ? `${Math.round((replied.length / submitted.length) * 100)}%` : '—',
  };
}
