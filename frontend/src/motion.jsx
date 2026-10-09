import React, { useEffect } from 'react';
import { AnimatePresence, motion, useReducedMotion } from 'motion/react';
import { flag } from './api';
import { easeOut } from './ui-motion';

const coordinates = {
  FR: [91, 66],
  DE: [100, 60],
  JP: [153, 75],
  IE: [79, 58],
  CA: [42, 45],
  GB: [83, 57],
  NL: [94, 59],
  US: [46, 72],
  KR: [146, 73],
  IN: [128, 91],
  AU: [155, 123],
  BR: [64, 116],
};

function fallbackCoordinate(code) {
  const letters = [...(code || 'WW')];
  const seed = letters.reduce((sum, letter) => sum + letter.charCodeAt(0), 0);
  return [35 + ((seed * 17) % 130), 38 + ((seed * 23) % 94)];
}

export function CountryTransition({ country, onFinished }) {
  const reduced = useReducedMotion();
  useEffect(() => {
    if (!country) return undefined;
    const timer = setTimeout(onFinished, reduced ? 100 : 1450);
    return () => clearTimeout(timer);
  }, [country, onFinished, reduced]);
  const [x, y] = country
    ? coordinates[country.code] || fallbackCoordinate(country.code)
    : [100, 85];
  return (
    <AnimatePresence>
      {country && (
        <motion.div
          className="country-transition"
          role="status"
          aria-live="polite"
          initial={reduced ? false : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          <motion.span
            className="travel-watermark"
            aria-hidden="true"
            initial={reduced ? false : { opacity: 0, x: 80 }}
            animate={{ opacity: 0.045, x: 0 }}
            transition={{ duration: 0.9, ease: easeOut }}
          >
            {country.name}
          </motion.span>
          <motion.div
            className="travel-card"
            initial={reduced ? false : { opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.55, ease: easeOut }}
          >
            <div className="globe-wrap" aria-hidden="true">
              <svg viewBox="0 0 200 170" className="travel-globe">
                <defs>
                  <linearGradient id="globe-fill" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0" stopColor="#92709c" />
                    <stop offset="1" stopColor="#a87061" />
                  </linearGradient>
                  <clipPath id="globe-clip">
                    <circle cx="100" cy="85" r="66" />
                  </clipPath>
                </defs>
                <circle className="globe-atmosphere" cx="100" cy="85" r="76" />
                <circle cx="100" cy="85" r="66" fill="url(#globe-fill)" />
                <g className="globe-grid" clipPath="url(#globe-clip)">
                  <ellipse cx="100" cy="85" rx="24" ry="66" />
                  <ellipse cx="100" cy="85" rx="49" ry="66" />
                  <path d="M34 85h132M42 53c35 15 81 15 116 0M42 117c35-15 81-15 116 0" />
                </g>
                <g className="globe-land" clipPath="url(#globe-clip)">
                  <path d="M30 57 48 38l24 5 10 17-14 12-4 22-21-2-13-18zM67 101l18 7 8 25-10 23-14-19zM103 36l29 1 16 19-13 13 20 11-5 27-24 4-18-16-13-22zM142 117l25 2 8 17-18 12-19-11z" />
                </g>
                <motion.circle
                  cx={x}
                  cy={y}
                  r="8"
                  fill="none"
                  stroke="#f3d4c5"
                  initial={reduced ? false : { opacity: 0, scale: 0.2 }}
                  animate={{ opacity: [0, 1, 0], scale: [0.2, 1, 2.4] }}
                  transition={{ duration: 1.1, delay: 0.35 }}
                />
                <circle className="destination-dot" cx={x} cy={y} r="3.5" />
              </svg>
            </div>
            <span className="travel-kicker">OPENING YOUR COUNTRY WORKSPACE</span>
            <strong>
              {flag(country.code)} {country.name}
            </strong>
            <small>Companies · contacts · CVs · applications</small>
            <motion.i
              className="travel-progress"
              initial={reduced ? false : { scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ duration: 1.15, ease: easeOut }}
            />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function SavedMoment({ moment }) {
  return (
    <AnimatePresence>
      {moment && (
        <motion.div
          className="saved-moment"
          role="status"
          aria-live="polite"
          initial={{ opacity: 0, y: 18, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 340, damping: 27 }}
        >
          <span className="saved-orbit" aria-hidden="true">
            <i />
            <i />
            <i />
          </span>
          <span className="saved-check" aria-hidden="true">
            ✓
          </span>
          <span>
            <strong>{moment.title}</strong>
            <small>{moment.subtitle}</small>
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
