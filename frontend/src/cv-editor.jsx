import React, { useEffect, useState } from 'react';
import { request } from './api';
import { ErrorBox, Modal } from './components';

export function CVEditor({ cv, onClose, onSaved }) {
  const [runs, setRuns] = useState(null);
  const [changes, setChanges] = useState({});
  const [name, setName] = useState(cv.name);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    request(`/resumes/${cv.id}/text`)
      .then((r) => {
        if (active) setRuns(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [cv.id]);
  const paragraphs = Object.groupBy(runs || [], (r) => r.paragraph);
  async function save(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      const result = await request(`/resumes/${cv.id}/versions`, {
        method: 'POST',
        body: JSON.stringify({ name, changes }),
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
    <Modal title={`Edit text · ${cv.name}`} wide onClose={onClose}>
      <form onSubmit={save}>
        <p className="editor-notice">
          Edit the text segments below. Fonts, styles, tables and images stay in the DOCX. Longer
          text may change line wrapping or page breaks. Saving creates a new file version;
          applications keep their original CV.
        </p>
        <ErrorBox error={error} />
        <label>
          New version name
          <input value={name} onChange={(e) => setName(e.target.value)} required maxLength="200" />
        </label>
        {!runs && !error && <p role="status">Reading document…</p>}
        <div className="document-editor">
          {Object.entries(paragraphs).map(([key, segments], i) => (
            <fieldset key={key}>
              <legend>
                Paragraph {i + 1} ·{' '}
                {segments[0].section.includes('header')
                  ? 'Header'
                  : segments[0].section.includes('footer')
                    ? 'Footer'
                    : 'Body'}
              </legend>
              {segments.map((run, j) => (
                <label className="run-label" key={run.id}>
                  <span>Text {j + 1}</span>
                  <textarea
                    aria-label={`Paragraph ${i + 1}, text ${j + 1}`}
                    rows={Math.max(1, Math.min(5, Math.ceil(run.text.length / 90)))}
                    value={changes[run.id] ?? run.text}
                    onChange={(e) => setChanges({ ...changes, [run.id]: e.target.value })}
                  />
                </label>
              ))}
            </fieldset>
          ))}
        </div>
        {runs?.length === 0 && <p>No editable text segments found in this document.</p>}
        <div className="form-footer">
          <a className="button" href={`/api/resumes/${cv.id}/file`}>
            Download original
          </a>
          <button
            className="primary"
            disabled={busy || !runs?.length || !Object.keys(changes).length}
          >
            {busy ? 'Saving…' : 'Save new CV version'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
