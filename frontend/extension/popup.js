const $ = (id) => document.getElementById(id);
const API = 'http://127.0.0.1:8000/api';
const origins = ['https://*.greenhouse.io/*', 'https://jobs.lever.co/*'];
let workspace;
let activeTab;
async function api(path, body, method = 'POST') {
  const response = await fetch(
    API + path,
    body
      ? { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
      : {},
  );
  const result = await response.json();
  if (!response.ok)
    throw new Error(
      typeof result.detail === 'string' ? result.detail : 'Please check the form details.',
    );
  return result;
}
function option(select, value, text) {
  const node = document.createElement('option');
  node.value = value;
  node.textContent = text;
  select.append(node);
}
function refresh() {
  const country = Number($('country').value);
  const previousResume = $('resume').value;
  $('company').replaceChildren();
  option($('company'), '', 'Choose company');
  workspace.companies
    .filter((c) => c.country_id === country)
    .forEach((c) => option($('company'), c.id, c.name));
  $('resume').replaceChildren();
  option($('resume'), '', 'None');
  workspace.resumes
    .filter((c) => c.country_id === country && !c.archived)
    .forEach((c) => option($('resume'), c.id, `${c.name} · v${c.version}`));
  if ([...$('resume').options].some((o) => o.value === previousResume))
    $('resume').value = previousResume;
}
function extractVisiblePage() {
  const visible = (selector) =>
    [...document.querySelectorAll(selector)]
      .find((node) => node.getClientRects().length)
      ?.innerText?.trim() || '';
  let job;
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    try {
      const value = JSON.parse(script.textContent);
      const list = Array.isArray(value) ? value : [value, ...(value['@graph'] || [])];
      job = list.find((x) => x['@type'] === 'JobPosting');
      if (job) break;
    } catch {
      /* A malformed structured-data block does not block manual capture. */
    }
  }
  return {
    title: job?.title || visible('h1') || document.title,
    company: job?.hiringOrganization?.name || '',
    url: location.href,
  };
}
async function initialize() {
  try {
    workspace = await api('/workspace');
    if (!workspace.countries.length)
      throw new Error('Add a country in the app first, then reopen this popup.');
    workspace.countries.forEach((c) => option($('country'), c.id, c.name));
    refresh();
    [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (activeTab && /^https?:/.test(activeTab.url || '')) {
      try {
        const [{ result }] = await chrome.scripting.executeScript({
          target: { tabId: activeTab.id },
          func: extractVisiblePage,
        });
        $('title').value = String(result.title).slice(0, 200);
        $('url').value = result.url;
        $('new-company').value = result.company;
        if (
          new URL(result.url).hostname.endsWith('linkedin.com') &&
          new URL(result.url).pathname.startsWith('/in/')
        ) {
          $('kind').value = 'contacts';
          toggleKind();
        }
      } catch {
        $('url').value = activeTab.url;
      }
      const key = `pending-${activeTab.id}`;
      const pending = (await chrome.storage.local.get(key))[key];
      if (pending && Date.now() - pending.time < 3600000) {
        $('status').value = 'Applied';
        $('message').textContent =
          'Possible application submission detected. Check the job details and confirm before saving.';
      } else
        $('message').textContent = 'Review the details below. Nothing is saved until you confirm.';
    } else
      $('message').textContent =
        'Open a job or contact page to capture it, or enter the details manually.';
    $('capture').hidden = false;
  } catch (e) {
    $('message').textContent = `${e.message} Ensure the backend is running on port 8000.`;
  }
  const enabled = (await chrome.scripting.getRegisteredContentScripts()).some(
    (s) => s.id === 'jobhunt-hints',
  );
  $('detect').textContent = enabled ? 'Disable submission hints' : 'Enable submission hints';
}
function toggleKind() {
  const contact = $('kind').value === 'contacts';
  $('job-fields').hidden = contact;
  $('contact-fields').hidden = !contact;
}
$('kind').addEventListener('change', toggleKind);
$('country').addEventListener('change', refresh);
$('capture').addEventListener('submit', async (event) => {
  event.preventDefault();
  $('save').disabled = true;
  try {
    const country = Number($('country').value);
    let companyId = Number($('company').value) || null;
    if (!companyId && $('new-company').value.trim()) {
      const name = $('new-company').value.trim();
      const match = workspace.companies.find(
        (c) => c.country_id === country && c.name.toLowerCase() === name.toLowerCase(),
      );
      const company = match || (await api('/companies', { country_id: country, name }));
      companyId = company.id;
      if (!match) workspace.companies.push(company);
      refresh();
      $('company').value = companyId;
    }
    const kind = $('kind').value;
    if (kind === 'applications' && !companyId)
      throw new Error('Choose or create a company for this application.');
    const payload =
      kind === 'applications'
        ? {
            company_id: companyId,
            title: $('title').value,
            job_url: $('url').value,
            status: $('status').value,
            resume_id: Number($('resume').value) || null,
            source: $('url').value ? new URL($('url').value).hostname : '',
            notes: $('notes').value,
          }
        : {
            country_id: country,
            company_id: companyId,
            name: $('title').value,
            linkedin: $('url').value,
            email: $('email').value,
            title: $('role').value,
            notes: $('notes').value,
          };
    const existing =
      kind === 'applications' && payload.job_url
        ? workspace.applications.find(
            (a) =>
              a.company_id === companyId &&
              a.job_url.replace(/#.*$/, '') === payload.job_url.replace(/#.*$/, ''),
          )
        : null;
    if (existing) {
      if (payload.status === 'Applied' && ['Saved', 'Contacted'].includes(existing.status))
        await api(
          `/applications/${existing.id}`,
          { status: 'Applied', resume_id: payload.resume_id },
          'PATCH',
        );
      else throw new Error('This job is already in your workspace. Open it there to update it.');
    } else await api(`/${kind}`, payload);
    if (activeTab?.id) {
      await chrome.storage.local.remove(`pending-${activeTab.id}`);
      await chrome.action.setBadgeText({ tabId: activeTab.id, text: '' });
    }
    $('message').textContent = 'Saved. Open the workspace to see your record.';
    $('capture').hidden = true;
  } catch (e) {
    $('message').textContent = e.message;
  } finally {
    $('save').disabled = false;
  }
});
$('detect').addEventListener('click', async () => {
  try {
    const enabled = (await chrome.scripting.getRegisteredContentScripts()).some(
      (s) => s.id === 'jobhunt-hints',
    );
    if (enabled) {
      await chrome.scripting.unregisterContentScripts({ ids: ['jobhunt-hints'] });
      await chrome.permissions.remove({ origins });
      $('detect').textContent = 'Enable submission hints';
    } else if (await chrome.permissions.request({ origins })) {
      await chrome.scripting.registerContentScripts([
        { id: 'jobhunt-hints', matches: origins, js: ['detect.js'], runAt: 'document_idle' },
      ]);
      $('detect').textContent = 'Disable submission hints';
    }
  } catch (e) {
    $('message').textContent = e.message;
  }
});
initialize();
