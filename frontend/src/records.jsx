import React, { useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { countryId, dateLabel, displayName, flag, labels, singular, statuses, today } from './api';
import { Badge, Empty } from './components';
import { easeOut } from './ui-motion';

export function Records({ kind, rows, data, open, add, update, query = '', compact = false }) {
  const [view, setView] = useState('table');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  const [company, setCompany] = useState('');
  const [cv, setCV] = useState('');
  const filtered = rows.filter((r) => {
    const companyName = data.companies.find((c) => c.id === r.company_id)?.name || '';
    return (
      `${Object.values(r).join(' ')} ${companyName}`.toLowerCase().includes(query.toLowerCase()) &&
      (!status || r.status === status) &&
      (!priority || r.priority === priority) &&
      (!company || r.company_id === Number(company)) &&
      (!cv || r.resume_id === Number(cv))
    );
  });
  if (!rows.length)
    return (
      <Empty
        title={`No ${labels[kind]?.toLowerCase() || kind} yet`}
        text={`Add a ${singular[kind]} to keep this part of your search organized.`}
        action={`Add ${singular[kind]}`}
        onAction={() => add(kind)}
      />
    );
  return (
    <>
      {!compact && (
        <div className="list-toolbar">
          <span>
            {filtered.length} {filtered.length === 1 ? singular[kind] : labels[kind]?.toLowerCase()}
          </span>
          {kind === 'applications' && (
            <>
              <select
                aria-label="Filter by status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="">All stages</option>
                {statuses.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <select
                aria-label="Filter by priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="">All priorities</option>
                {['High', 'Medium', 'Low'].map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </select>
              <select
                aria-label="Filter by company"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              >
                <option value="">All companies</option>
                {data.companies.map((c) => (
                  <option value={c.id} key={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <select aria-label="Filter by CV" value={cv} onChange={(e) => setCV(e.target.value)}>
                <option value="">All CVs</option>
                {data.resumes.map((c) => (
                  <option value={c.id} key={c.id}>
                    {c.name} v{c.version}
                  </option>
                ))}
              </select>
              <div className="segmented">
                <button
                  className={view === 'table' ? 'selected' : ''}
                  onClick={() => setView('table')}
                >
                  Table
                </button>
                <button
                  className={view === 'board' ? 'selected' : ''}
                  onClick={() => setView('board')}
                >
                  Board
                </button>
              </div>
            </>
          )}
        </div>
      )}
      {kind === 'countries' ? (
        <div className="country-cards">
          {filtered.map((c, index) => (
            <motion.button
              layout
              className="country-card"
              key={c.id}
              onClick={() => open(kind, c.id)}
              initial={{ opacity: 0, y: 16, scale: 0.985 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.4, delay: Math.min(index * 0.04, 0.2), ease: easeOut }}
            >
              <div>
                <span>{flag(c.code)}</span>
                <Badge>{c.priority}</Badge>
              </div>
              <h2>{c.name}</h2>
              <p>{c.target_roles || 'Set your target roles and strategy'}</p>
              <footer>
                <span>{data.companies.filter((x) => x.country_id === c.id).length} companies</span>
                <span>{data.resumes.filter((x) => x.country_id === c.id).length} CVs</span>
                <span>{data.contacts.filter((x) => x.country_id === c.id).length} contacts</span>
              </footer>
            </motion.button>
          ))}
        </div>
      ) : kind === 'applications' && view === 'board' ? (
        <div className="board">
          {statuses.map((s) => (
            <section
              className="board-column"
              key={s}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const id = Number(e.dataTransfer.getData('text/plain'));
                if (rows.some((r) => r.id === id)) update('applications', id, { status: s });
              }}
            >
              <h3>
                {s}
                <span>{filtered.filter((a) => a.status === s).length}</span>
              </h3>
              {filtered
                .filter((a) => a.status === s)
                .map((a) => (
                  <motion.article
                    layout
                    className="application-card"
                    key={a.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData('text/plain', String(a.id))}
                    initial={{ opacity: 0, y: 7 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, ease: easeOut }}
                  >
                    <button className="row-link" onClick={() => open(kind, a.id)}>
                      <b>{a.title}</b>
                      <small>{data.companies.find((c) => c.id === a.company_id)?.name}</small>
                    </button>
                    <Badge>{a.priority}</Badge>
                    <select
                      aria-label={`Status for ${a.title}`}
                      value={a.status}
                      onChange={(e) => update('applications', a.id, { status: e.target.value })}
                    >
                      {statuses.map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </motion.article>
                ))}
            </section>
          ))}
        </div>
      ) : (
        <div className="table-scroll panel">
          <table>
            <thead>
              <tr>
                <th>
                  {kind === 'resumes' ? 'CV version' : kind === 'contacts' ? 'Person' : 'Name'}
                </th>
                <th>{['applications', 'contacts'].includes(kind) ? 'Company' : 'Country'}</th>
                <th>
                  {kind === 'resumes'
                    ? 'Role / language'
                    : kind === 'followups'
                      ? 'Due'
                      : kind === 'interviews'
                        ? 'Scheduled'
                        : 'Details'}
                </th>
                <th>Status</th>
                <th>
                  <span className="sr-only">Open</span>
                </th>
              </tr>
            </thead>
            <motion.tbody layout>
              <AnimatePresence initial={false} mode="popLayout">
                {filtered.map((r) => {
                  const country = data.countries.find((c) => c.id === countryId(data, kind, r));
                  const comp = data.companies.find((c) => c.id === r.company_id);
                  return (
                    <motion.tr
                      layout="position"
                      key={r.id}
                      initial={{ opacity: 0, y: 7 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={{ duration: 0.25, ease: easeOut }}
                    >
                      <td>
                        <button className="row-link" onClick={() => open(kind, r.id)}>
                          <b>{displayName(kind, r)}</b>
                          <small>
                            {kind === 'resumes'
                              ? `${r.filename} · v${r.version}`
                              : kind === 'contacts'
                                ? r.title
                                : ''}
                          </small>
                        </button>
                      </td>
                      <td>
                        {['applications', 'contacts'].includes(kind)
                          ? comp?.name || 'Independent contact'
                          : country?.name || '—'}
                      </td>
                      <td>
                        {kind === 'applications'
                          ? r.source || '—'
                          : kind === 'resumes'
                            ? [r.target_role, r.language].filter(Boolean).join(' · ') || '—'
                            : kind === 'followups'
                              ? dateLabel(r.due_date)
                              : kind === 'interviews'
                                ? `${dateLabel(r.scheduled_at)} · ${new Date(r.scheduled_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                                : kind === 'contacts'
                                  ? r.email || '—'
                                  : r.email || r.website || '—'}
                      </td>
                      <td>
                        {kind === 'applications' ? (
                          <select
                            className="status-select"
                            aria-label={`Status for ${r.title}`}
                            value={r.status}
                            onChange={(e) => update(kind, r.id, { status: e.target.value })}
                          >
                            {statuses.map((s) => (
                              <option key={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          <Badge>
                            {kind === 'resumes'
                              ? r.archived
                                ? 'Archived'
                                : 'Active'
                              : kind === 'followups'
                                ? r.completed
                                  ? 'Completed'
                                  : r.due_date < today()
                                    ? 'Overdue'
                                    : 'Open'
                                : r.status || r.relationship || r.sponsorship}
                          </Badge>
                        )}
                      </td>
                      <td>
                        <button
                          className="text-button"
                          onClick={() => open(kind, r.id)}
                          aria-label={`Open ${displayName(kind, r)}`}
                        >
                          ↗
                        </button>
                      </td>
                    </motion.tr>
                  );
                })}
              </AnimatePresence>
            </motion.tbody>
          </table>
        </div>
      )}
      {!filtered.length && (
        <p className="quiet-state">No matches. Try another search or clear the filters.</p>
      )}
    </>
  );
}
