import React, { Suspense, lazy, useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { request, countryId, dateLabel, displayName, flag, labels, singular } from './api';
import { ErrorBox, Icon, Modal, Empty } from './components';
import { RecordForm, UploadForm } from './forms';
import { Dashboard, Analytics } from './dashboard';
import { Records } from './records';
import { Detail } from './detail';
import { CVEditor } from './cv-editor';
import { CountryTransition, SavedMoment } from './motion';
import { AnimatePresence, MotionConfig, motion } from 'motion/react';
import { PageStage, easeOut } from './ui-motion';
import './styles.css';

const CountryWizard = lazy(() => import('./country-wizard'));

const navigation = [
  'dashboard',
  'countries',
  'companies',
  'applications',
  'contacts',
  'resumes',
  'followups',
  'interviews',
  'analytics',
];
function readRoute() {
  const [page = 'dashboard', id] = location.hash.replace(/^#\/?/, '').split('/');
  return { page: navigation.includes(page) ? page : 'dashboard', id: id ? Number(id) : null };
}
function App() {
  const [route, setRoute] = useState(readRoute);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [country, setCountry] = useState(
    () => Number(localStorage.getItem('jobhunt-country')) || 0,
  );
  const [query, setQuery] = useState('');
  const [form, setForm] = useState(null);
  const [upload, setUpload] = useState(null);
  const [editingCV, setEditingCV] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [menu, setMenu] = useState(false);
  const [notice, setNotice] = useState('');
  const [saving, setSaving] = useState(false);
  const [transition, setTransition] = useState(null);
  const [savedMoment, setSavedMoment] = useState(null);
  const [countryWizard, setCountryWizard] = useState(false);
  const reload = useCallback(async () => {
    const value = await request('/workspace');
    setData(value);
    setCountry((current) => (value.countries.some((c) => c.id === current) ? current : 0));
    return value;
  }, []);
  useEffect(() => {
    reload()
      .catch((e) => setError(`Could not connect to the API: ${e.message}`))
      .finally(() => setLoading(false));
  }, [reload]);
  useEffect(() => {
    const refresh = () => {
      if (!document.hidden) reload().catch(() => {});
    };
    const timer = setInterval(refresh, 15000);
    addEventListener('focus', refresh);
    return () => {
      clearInterval(timer);
      removeEventListener('focus', refresh);
    };
  }, [reload]);
  useEffect(() => {
    const change = () => {
      setRoute(readRoute());
      setQuery('');
      setMenu(false);
    };
    addEventListener('hashchange', change);
    return () => removeEventListener('hashchange', change);
  }, []);
  useEffect(() => {
    localStorage.setItem('jobhunt-country', String(country));
  }, [country]);
  useEffect(() => {
    if (notice) {
      const timer = setTimeout(() => setNotice(''), 4500);
      return () => clearTimeout(timer);
    }
  }, [notice]);
  useEffect(() => {
    if (savedMoment) {
      const timer = setTimeout(() => setSavedMoment(null), 2800);
      return () => clearTimeout(timer);
    }
  }, [savedMoment]);
  const navigate = (page, id) => {
    location.hash = `/${page}${id ? `/${id}` : ''}`;
  };
  function add(kind, defaults = {}) {
    const initial = { country_id: country || '', ...defaults };
    if (kind === 'countries') {
      setCountryWizard(true);
      return;
    }
    if (kind !== 'countries' && !data.countries.length) {
      setNotice('Add a country first.');
      setCountryWizard(true);
      return;
    }
    if (
      kind === 'applications' &&
      !data.companies.some(
        (c) => !initial.country_id || c.country_id === Number(initial.country_id),
      )
    ) {
      setNotice('Add a company in this country first.');
      setForm({ kind: 'companies', defaults: initial });
      return;
    }
    if (kind === 'interviews' && !data.applications.length) {
      setNotice('Add an application before scheduling an interview.');
      navigate('applications');
      return;
    }
    if (kind === 'resumes') {
      setUpload({ country: initial.country_id });
      return;
    }
    setForm({ kind, defaults: initial });
  }
  async function update(kind, id, patch) {
    setError('');
    setSaving(true);
    try {
      await request(`/${kind}/${id}`, { method: 'PATCH', body: JSON.stringify(patch) });
      await reload();
      setNotice('Saved.');
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }
  async function saved(record, kind) {
    await reload();
    const names = {
      companies: 'Company added',
      applications: 'Application added',
      contacts: 'Contact added',
      resumes: 'CV saved',
      countries: 'Country added',
      interviews: 'Interview scheduled',
      followups: 'Follow-up scheduled',
      interactions: 'Conversation recorded',
    };
    setSavedMoment({ title: names[kind] || 'Saved' });
    if (record?.id && kind) {
      if (kind === 'interactions') navigate('contacts', record.contact_id);
      else navigate(kind, record.id);
    }
  }
  const activeCountry = data?.countries.find((c) => c.id === country);
  const scope = data
    ? Object.fromEntries(
        Object.entries(data).map(([kind, records]) => [
          kind,
          kind === 'status_history'
            ? records
            : records.filter((r) => !country || countryId(data, kind, r) === country),
        ]),
      )
    : null;
  const current = data?.[route.page]?.find((r) => r.id === route.id);
  const title =
    route.page === 'dashboard'
      ? 'Overview'
      : route.page === 'analytics'
        ? 'Analytics'
        : labels[route.page];
  const searchResults =
    query && data
      ? navigation
          .filter((k) => data[k])
          .flatMap((kind) =>
            scope[kind]
              .filter((r) =>
                `${displayName(kind, r)} ${r.notes || ''} ${r.email || ''} ${data.companies.find((c) => c.id === r.company_id)?.name || ''}`
                  .toLowerCase()
                  .includes(query.toLowerCase()),
              )
              .map((r) => ({ kind, r })),
          )
          .slice(0, 10)
      : [];
  const pageIdentity = `${route.page}-${route.id || 'index'}-${country}`;
  return (
    <MotionConfig reducedMotion="user">
      <div className="app-shell">
        <aside className={`sidebar ${menu ? 'show' : ''}`}>
          <a className="brand" href="#/dashboard">
            <span>Job Hunt OS</span>
          </a>
          <p className="nav-label">YOUR WORKSPACE</p>
          <nav>
            {navigation.map((page) => (
              <a key={page} href={`#/${page}`} className={route.page === page ? 'active' : ''}>
                {route.page === page && (
                  <motion.span
                    className="nav-active-glow"
                    layoutId="active-navigation"
                    transition={{ type: 'spring', stiffness: 340, damping: 31 }}
                  />
                )}
                <Icon name={page} />
                <span>{labels[page] || (page === 'dashboard' ? 'Overview' : 'Analytics')}</span>
                {page === 'followups' &&
                  scope?.followups.filter((f) => !f.completed).length > 0 && (
                    <small>{scope.followups.filter((f) => !f.completed).length}</small>
                  )}
              </a>
            ))}
          </nav>
          <div className="sidebar-bottom">
            <a href="/api/export">Export data</a>
            <small>Stored locally</small>
          </div>
        </aside>
        <div className="workspace">
          <header className="topbar">
            <button
              className="mobile-menu icon-button"
              aria-label="Toggle navigation"
              onClick={() => setMenu(!menu)}
            >
              ☰
            </button>
            <div className="country-selector">
              <Icon name="countries" />
              <select
                aria-label="Active country"
                value={country}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  const selected = data?.countries.find((item) => item.id === next);
                  if (!selected) {
                    setCountry(0);
                    if (route.id) navigate(route.page);
                    return;
                  }
                  setTransition({ country: selected, next });
                }}
              >
                <option value="0">All countries</option>
                {data?.countries.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="global-search">
              <Icon name="search" size={17} />
              <input
                aria-label="Search workspace"
                placeholder="Search your workspace…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              {query && (
                <button
                  aria-label="Clear search"
                  className="icon-button"
                  onClick={() => setQuery('')}
                >
                  ×
                </button>
              )}
              {query && (
                <div className="search-results">
                  {searchResults.map(({ kind, r }) => (
                    <button
                      key={`${kind}-${r.id}`}
                      onClick={() => {
                        navigate(kind, r.id);
                        setQuery('');
                      }}
                    >
                      <Icon name={kind} />
                      <span>
                        {displayName(kind, r)}
                        <small>{labels[kind]}</small>
                      </span>
                    </button>
                  ))}
                  {!searchResults.length && <p>No matching records in this country scope.</p>}
                </div>
              )}
            </div>
            <span className="top-date">{dateLabel(new Date().toISOString())}</span>
            <span className="local-avatar" title="Local workspace">
              J
            </span>
          </header>
          <main>
            <ErrorBox error={error} />
            {saving && (
              <div className="saving" role="status">
                Saving…
              </div>
            )}
            <AnimatePresence>
              {notice && (
                <motion.div
                  className="toast"
                  role="status"
                  initial={{ opacity: 0, y: 14, scale: 0.96 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: 8, scale: 0.98 }}
                  transition={{ duration: 0.3, ease: easeOut }}
                >
                  {notice}
                </motion.div>
              )}
            </AnimatePresence>
            <SavedMoment moment={savedMoment} />
            <CountryTransition
              country={transition?.country}
              onFinished={() => {
                if (!transition) return;
                setCountry(transition.next);
                setTransition(null);
                if (route.id) navigate(route.page);
              }}
            />
            <AnimatePresence mode="wait" initial={false}>
              <PageStage key={pageIdentity} identity={pageIdentity}>
                {loading ? (
                  <div className="loading" role="status">
                    Opening your workspace…
                  </div>
                ) : !data ? (
                  <Empty
                    title="The backend is unavailable"
                    text="Start the API, then retry to load your saved records."
                    action="Retry"
                    onAction={async () => {
                      setError('');
                      setLoading(true);
                      try {
                        await reload();
                      } catch (e) {
                        setError(e.message);
                      } finally {
                        setLoading(false);
                      }
                    }}
                  />
                ) : route.id ? (
                  current ? (
                    <Detail
                      key={`${route.page}-${route.id}`}
                      kind={route.page}
                      record={current}
                      data={data}
                      open={navigate}
                      add={add}
                      edit={(kind, record) => setForm({ kind, record })}
                      remove={(kind, record) => setDeleting({ kind, record })}
                      update={update}
                      editCV={setEditingCV}
                      selectCountry={(id) => {
                        setCountry(id);
                        navigate('dashboard');
                      }}
                    />
                  ) : (
                    <Empty
                      title="Record not found"
                      text="This record may have been deleted."
                      action="Back to list"
                      onAction={() => navigate(route.page)}
                    />
                  )
                ) : (
                  <>
                    <div className="page-header">
                      <div>
                        {activeCountry && (
                          <div className="eyebrow">
                            {flag(activeCountry.code)} {activeCountry.name.toUpperCase()}
                          </div>
                        )}
                        <h1>{title}</h1>
                      </div>
                      {labels[route.page] && (
                        <button className="primary" onClick={() => add(route.page)}>
                          ＋ Add {singular[route.page]}
                        </button>
                      )}
                    </div>
                    {route.page === 'dashboard' ? (
                      <Dashboard
                        data={data}
                        scope={scope}
                        open={navigate}
                        add={add}
                        navigate={navigate}
                        toggleFollowup={(r) =>
                          update('followups', r.id, { completed: !r.completed })
                        }
                      />
                    ) : route.page === 'analytics' ? (
                      <Analytics data={data} scope={scope} />
                    ) : (
                      <Records
                        key={`${route.page}-${country}`}
                        kind={route.page}
                        rows={scope[route.page]}
                        data={data}
                        query={query}
                        open={navigate}
                        add={add}
                        update={update}
                      />
                    )}
                  </>
                )}
              </PageStage>
            </AnimatePresence>
          </main>
        </div>
        {countryWizard && (
          <Suspense fallback={<div className="modal-loader">Loading country map…</div>}>
            <CountryWizard
              existingCountries={data.countries}
              onClose={() => setCountryWizard(false)}
              onSaved={(record) => {
                setCountryWizard(false);
                setCountry(record.id);
                saved(record, 'countries');
              }}
            />
          </Suspense>
        )}
        {form && (
          <RecordForm
            {...form}
            data={data}
            onClose={() => setForm(null)}
            onSaved={(r) => saved(r, form.kind)}
          />
        )}{' '}
        {upload && (
          <UploadForm {...upload} data={data} onClose={() => setUpload(null)} onSaved={saved} />
        )}{' '}
        {editingCV && (
          <CVEditor
            cv={editingCV}
            onClose={() => setEditingCV(null)}
            onSaved={(r) => saved(r, 'resumes')}
          />
        )}{' '}
        {deleting && (
          <DeleteDialog
            target={deleting}
            onClose={() => setDeleting(null)}
            onDeleted={async () => {
              await reload();
              navigate(deleting.kind);
              setDeleting(null);
              setNotice('Record deleted.');
            }}
          />
        )}
      </div>
    </MotionConfig>
  );
}
function DeleteDialog({ target, onClose, onDeleted }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function confirm() {
    setBusy(true);
    setError('');
    try {
      await request(`/${target.kind}/${target.record.id}`, { method: 'DELETE' });
      await onDeleted();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal title={`Delete ${singular[target.kind]}?`} onClose={onClose}>
      <ErrorBox error={error} />
      <p>
        Delete “{displayName(target.kind, target.record)}”? This cannot be undone. Records with
        linked data cannot be deleted.
      </p>
      <div className="form-footer">
        <button onClick={onClose}>Keep record</button>
        <button className="delete-button" onClick={confirm} disabled={busy}>
          {busy ? 'Deleting…' : 'Delete record'}
        </button>
      </div>
    </Modal>
  );
}
createRoot(document.getElementById('root')).render(<App />);
