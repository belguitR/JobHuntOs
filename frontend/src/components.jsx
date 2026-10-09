import React, { useEffect, useRef } from 'react';

export function Icon({ name, size = 20 }) {
  const paths = {
    dashboard: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    countries: (
      <>
        <circle cx="12" cy="12" r="9" />
        <ellipse cx="12" cy="12" rx="4" ry="9" />
        <path d="M3 12h18" />
      </>
    ),
    companies: (
      <>
        <path d="M4 21V5l9-2v18M13 9h7v12M2 21h20M7 8h3M7 12h3M7 16h3M16 12h1M16 16h1" />
      </>
    ),
    contacts: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M18 15a5 5 0 0 1 3 5" />
      </>
    ),
    applications: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M8 5V3h8v2M3 11h18M10 11v3h4v-3" />
      </>
    ),
    resumes: (
      <>
        <path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6" />
      </>
    ),
    interviews: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M7 3v5M17 3v5M3 11h18M8 15h2M14 15h2" />
      </>
    ),
    followups: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v6l4 2" />
      </>
    ),
    analytics: (
      <>
        <path d="M4 3v18h18M8 17v-5M13 17V8M18 17V4" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 6 6" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.applications}
    </svg>
  );
}
export function Badge({ children }) {
  return (
    <span
      className={`badge ${['Rejected', 'Ghosted', 'Overdue'].includes(children) ? 'danger' : ['Offer', 'Accepted', 'Completed'].includes(children) ? 'success' : ''}`}
    >
      {children}
    </span>
  );
}
export function Empty({ title, text, action, onAction }) {
  return (
    <div className="empty">
      <span className="empty-symbol">✦</span>
      <h2>{title}</h2>
      <p>{text}</p>
      {action && (
        <button className="primary" onClick={onAction}>
          ＋ {action}
        </button>
      )}
    </div>
  );
}
export function Modal({ title, children, onClose, wide = false, className = '' }) {
  const ref = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    const dialog = ref.current;
    dialog.showModal();
    return () => {
      dialog.close();
      previous?.focus?.();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`modal ${wide ? 'modal-wide' : ''} ${className}`.trim()}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <div className="modal-heading">
        <h2>{title}</h2>
        <button className="icon-button" aria-label="Close dialog" onClick={onClose}>
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function ErrorBox({ error }) {
  return error ? (
    <div role="alert" className="error">
      {error}
    </div>
  ) : null;
}
export function Section({ title, action, children }) {
  return (
    <section className="panel">
      <div className="section-heading">
        <h2>{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
export function External({ url, children }) {
  return url && /^https?:\/\//i.test(url) ? (
    <a href={url} target="_blank" rel="noreferrer">
      {children || url} ↗
    </a>
  ) : (
    <span>{children || '—'}</span>
  );
}
