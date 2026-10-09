import React, { useEffect, useState } from 'react';
import {
  animate,
  motion,
  useMotionValue,
  useMotionValueEvent,
  useReducedMotion,
} from 'motion/react';

export const easeOut = [0.22, 1, 0.36, 1];
export const softSpring = { type: 'spring', stiffness: 280, damping: 30, mass: 0.75 };

export function PageStage({ identity, children }) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      key={identity}
      className="page-stage"
      initial={reduced ? false : { opacity: 0, y: 12, filter: 'blur(5px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={reduced ? undefined : { opacity: 0, y: -6, filter: 'blur(3px)' }}
      transition={{ duration: 0.42, ease: easeOut }}
    >
      {children}
    </motion.div>
  );
}

export function AnimatedNumber({ value, className = '' }) {
  const numeric = Number(value) || 0;
  const reduced = useReducedMotion();
  const motionValue = useMotionValue(reduced ? numeric : 0);
  const [display, setDisplay] = useState(reduced ? numeric : 0);

  useMotionValueEvent(motionValue, 'change', (latest) => setDisplay(Math.round(latest)));
  useEffect(() => {
    if (reduced) {
      motionValue.set(numeric);
      setDisplay(numeric);
      return undefined;
    }
    const controls = animate(motionValue, numeric, { duration: 0.7, ease: easeOut });
    return controls.stop;
  }, [motionValue, numeric, reduced]);

  return <strong className={className}>{display}</strong>;
}

export const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.065, delayChildren: 0.04 } },
};

export const rise = {
  hidden: { opacity: 0, y: 14 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.46, ease: easeOut } },
};

export { motion };
