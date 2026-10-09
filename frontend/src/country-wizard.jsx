import React, { Component, useEffect, useMemo, useRef, useState } from 'react';
import Globe from 'react-globe.gl';
import * as THREE from 'three';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { feature } from 'topojson-client';
import world from 'world-atlas/countries-110m.json';
import countries from 'world-countries';
import { request } from './api';
import { ErrorBox, Modal } from './components';

const polygons = feature(world, world.objects.countries).features;

function countrySearchText(country) {
  return [
    country.name.common,
    country.name.official,
    country.cca2,
    country.cca3,
    country.cioc,
    ...(country.altSpellings || []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase();
}

const catalogue = countries
  .filter((country) => country.status === 'officially-assigned' && country.cca2)
  .map((country) => ({ ...country, searchText: countrySearchText(country) }))
  .sort((a, b) => a.name.common.localeCompare(b.name.common));

class GlobeBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="globe-fallback" role="status">
          <p>3D map unavailable.</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function WorldGlobe({ selected, onReady }) {
  const globe = useRef(null);
  const material = useMemo(
    () =>
      new THREE.MeshPhongMaterial({
        color: '#25152d',
        emissive: '#130a19',
        shininess: 10,
        transparent: true,
        opacity: 0.98,
      }),
    [],
  );

  useEffect(() => () => material.dispose(), [material]);

  useEffect(() => {
    if (!globe.current || !selected) return;
    const [lat, lng] = selected.latlng;
    globe.current.pointOfView({ lat, lng, altitude: 1.65 }, 1350);
    const controls = globe.current.controls();
    if (controls) controls.autoRotate = false;
  }, [selected]);

  function ready() {
    const controls = globe.current?.controls();
    if (controls) {
      controls.autoRotate = !matchMedia('(prefers-reduced-motion: reduce)').matches;
      controls.autoRotateSpeed = 0.42;
      controls.enablePan = false;
      controls.enableZoom = false;
    }
    globe.current?.pointOfView({ lat: 18, lng: 5, altitude: 2.15 }, 0);
    onReady();
  }

  const selectedId = selected?.ccn3;
  const marker = selected
    ? [{ lat: selected.latlng[0], lng: selected.latlng[1], country: selected.name.common }]
    : [];

  return (
    <GlobeBoundary>
      <Globe
        ref={globe}
        width={760}
        height={560}
        backgroundColor="rgba(0,0,0,0)"
        globeMaterial={material}
        atmosphereColor="#dba6bf"
        atmosphereAltitude={0.19}
        polygonsData={polygons}
        polygonCapColor={(shape) =>
          String(shape.id).padStart(3, '0') === selectedId ? '#efb08f' : '#765270'
        }
        polygonSideColor={() => '#2b1731'}
        polygonStrokeColor={() => '#aa849f'}
        polygonAltitude={(shape) =>
          String(shape.id).padStart(3, '0') === selectedId ? 0.045 : 0.007
        }
        polygonsTransitionDuration={650}
        pointsData={marker}
        pointLat="lat"
        pointLng="lng"
        pointColor={() => '#fff1df'}
        pointAltitude={0.1}
        pointRadius={0.22}
        ringsData={marker}
        ringLat="lat"
        ringLng="lng"
        ringColor={() => '#f4b292'}
        ringMaxRadius={4}
        ringPropagationSpeed={2.1}
        ringRepeatPeriod={900}
        onGlobeReady={ready}
        enablePointerInteraction={false}
      />
    </GlobeBoundary>
  );
}

export default function CountryWizard({ existingCountries, onClose, onSaved }) {
  const reduced = useReducedMotion();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [globeReady, setGlobeReady] = useState(false);
  const [showPlan, setShowPlan] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [values, setValues] = useState({
    priority: 'Medium',
    target_roles: '',
    salary_notes: '',
    visa_notes: '',
    language_notes: '',
    job_boards: '',
    notes: '',
  });
  const existingCodes = useMemo(
    () => new Set(existingCountries.map((country) => country.code)),
    [existingCountries],
  );
  const suggestions = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase();
    if (!needle || selected?.name.common === query) return [];
    return catalogue
      .filter((country) => country.searchText.includes(needle))
      .sort((a, b) => {
        const aStarts = a.name.common.toLocaleLowerCase().startsWith(needle) ? 0 : 1;
        const bStarts = b.name.common.toLocaleLowerCase().startsWith(needle) ? 0 : 1;
        return aStarts - bStarts || a.name.common.localeCompare(b.name.common);
      })
      .slice(0, 7);
  }, [query, selected]);

  useEffect(() => {
    if (!selected) {
      setShowPlan(false);
      return undefined;
    }
    const timer = setTimeout(() => setShowPlan(true), 720);
    return () => clearTimeout(timer);
  }, [selected]);

  function selectCountry(country) {
    if (existingCodes.has(country.cca2)) return;
    setSelected(country);
    setQuery(country.name.common);
    setShowPlan(false);
    setError('');
    setValues((current) => ({
      ...current,
      language_notes: Object.values(country.languages || {}).join(', '),
    }));
  }

  function update(key, value) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      const saved = await request('/countries', {
        method: 'POST',
        body: JSON.stringify({
          name: selected.name.common,
          code: selected.cca2,
          ...values,
        }),
      });
      onSaved(saved);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  const currency = selected
    ? Object.entries(selected.currencies || {})
        .map(([code, item]) => `${item.symbol || code} ${code}`)
        .join(' · ')
    : '';

  return (
    <Modal
      title="Add a country"
      onClose={onClose}
      className={`country-studio ${selected ? 'country-selected' : ''}`}
    >
      <p className="country-studio-lead">
        {selected
          ? 'Review the country settings before saving.'
          : 'Search by country name or code.'}
      </p>
      <AnimatePresence initial={false}>
        {!selected && (
          <motion.div
            className="country-search-wrap"
            initial={reduced ? false : { opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
          >
            <span aria-hidden="true">⌕</span>
            <input
              autoFocus
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search countries"
              aria-label="Search for a country"
              aria-autocomplete="list"
              aria-controls="country-suggestions"
            />
            {query && (
              <button
                className="country-search-clear"
                type="button"
                aria-label="Clear country search"
                onClick={() => setQuery('')}
              >
                ×
              </button>
            )}
            <AnimatePresence>
              {suggestions.length > 0 && (
                <motion.div
                  className="country-suggestions"
                  id="country-suggestions"
                  role="listbox"
                  initial={reduced ? false : { opacity: 0, y: -8, scale: 0.985 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -5, scale: 0.99 }}
                  transition={{ duration: 0.2 }}
                >
                  {suggestions.map((country, index) => {
                    const exists = existingCodes.has(country.cca2);
                    return (
                      <motion.button
                        key={country.cca2}
                        type="button"
                        role="option"
                        aria-selected={false}
                        disabled={exists}
                        onClick={() => selectCountry(country)}
                        initial={reduced ? false : { opacity: 0, x: -7 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: Math.min(index * 0.025, 0.12) }}
                      >
                        <b>{country.flag}</b>
                        <span>
                          <strong>{country.name.common}</strong>
                          <small>
                            {country.capital?.[0] || country.region} ·{' '}
                            {country.subregion || country.region}
                          </small>
                        </span>
                        <em>{exists ? 'Already added' : country.cca2}</em>
                      </motion.button>
                    );
                  })}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      <div className={`country-explorer ${selected ? 'has-selection' : ''}`}>
        <div className={`globe-stage ${globeReady ? 'is-ready' : ''}`}>
          <WorldGlobe selected={selected} onReady={() => setGlobeReady(true)} />
          {!selected && (
            <div className="globe-intro">
              <span>Drag to rotate</span>
            </div>
          )}
        </div>

        <AnimatePresence>
          {selected && showPlan && (
            <motion.form
              className="country-plan"
              onSubmit={submit}
              initial={reduced ? false : { opacity: 0, x: 36, clipPath: 'inset(0 0 0 12%)' }}
              animate={{ opacity: 1, x: 0, clipPath: 'inset(0 0 0 0%)' }}
              exit={{ opacity: 0, x: 18 }}
              transition={{ type: 'spring', stiffness: 180, damping: 24, mass: 0.85 }}
            >
              <div className="selected-country">
                <span>{selected.flag}</span>
                <div>
                  <small>
                    {selected.region} · {selected.cca3}
                  </small>
                  <h3>{selected.name.common}</h3>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setSelected(null);
                    setQuery('');
                  }}
                >
                  Change
                </button>
              </div>
              <div className="country-facts">
                <span>
                  <small>Capital</small>
                  {selected.capital?.[0] || '—'}
                </span>
                <span>
                  <small>Currency</small>
                  {currency || '—'}
                </span>
              </div>
              <div className="plan-heading">
                <div>
                  <h3>Search settings</h3>
                </div>
              </div>
              <div className="country-plan-grid">
                <label>
                  Priority
                  <select
                    value={values.priority}
                    onChange={(e) => update('priority', e.target.value)}
                  >
                    <option>High</option>
                    <option>Medium</option>
                    <option>Low</option>
                  </select>
                </label>
                <label>
                  Target roles
                  <input
                    value={values.target_roles}
                    onChange={(e) => update('target_roles', e.target.value)}
                    placeholder="Backend Engineer, SRE…"
                  />
                </label>
                <label>
                  Salary target
                  <input
                    value={values.salary_notes}
                    onChange={(e) => update('salary_notes', e.target.value)}
                    placeholder="€70k–€85k / year"
                  />
                </label>
                <label>
                  Languages
                  <input
                    value={values.language_notes}
                    onChange={(e) => update('language_notes', e.target.value)}
                  />
                </label>
                <label className="span-two">
                  Visa & work authorization
                  <textarea
                    rows="2"
                    value={values.visa_notes}
                    onChange={(e) => update('visa_notes', e.target.value)}
                    placeholder="Sponsorship needs, permit notes…"
                  />
                </label>
                <label className="span-two">
                  Job boards & sources
                  <input
                    value={values.job_boards}
                    onChange={(e) => update('job_boards', e.target.value)}
                    placeholder="LinkedIn, local boards, communities…"
                  />
                </label>
              </div>
              <ErrorBox error={error} />
              <button className="primary country-save" disabled={busy}>
                {busy ? 'Creating workspace…' : `Create ${selected.name.common} workspace →`}
              </button>
            </motion.form>
          )}
        </AnimatePresence>
      </div>
    </Modal>
  );
}
