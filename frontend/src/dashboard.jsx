import React from 'react';
import { useMotionValue, useReducedMotion, useSpring, useTransform } from 'motion/react';
import { dateLabel, flag, stats, terminal, today } from './api';
import { Badge, Icon, Section } from './components';
import { AnimatedNumber, easeOut, motion, rise, stagger } from './ui-motion';

function Welcome({ add }) {
  const reduced = useReducedMotion();
  const pointerX = useMotionValue(0.5);
  const pointerY = useMotionValue(0.5);
  const rotateX = useSpring(useTransform(pointerY, [0, 1], [1.6, -1.6]), {
    stiffness: 100,
    damping: 20,
  });
  const rotateY = useSpring(useTransform(pointerX, [0, 1], [-2.2, 2.2]), {
    stiffness: 100,
    damping: 20,
  });
  const glowX = useTransform(pointerX, [0, 1], ['-18%', '48%']);
  const glowY = useTransform(pointerY, [0, 1], ['-22%', '34%']);

  function move(event) {
    if (reduced) return;
    const bounds = event.currentTarget.getBoundingClientRect();
    pointerX.set((event.clientX - bounds.left) / bounds.width);
    pointerY.set((event.clientY - bounds.top) / bounds.height);
  }

  function reset() {
    pointerX.set(0.5);
    pointerY.set(0.5);
  }

  return (
    <motion.div className="welcome" variants={stagger} initial="hidden" animate="visible">
      <motion.div
        className="welcome-art"
        variants={rise}
        onPointerMove={move}
        onPointerLeave={reset}
        style={reduced ? undefined : { rotateX, rotateY, transformPerspective: 1100 }}
      >
        <motion.div className="welcome-ambient" style={{ x: glowX, y: glowY }} />
        <h2>
          <motion.span variants={rise}>Add your first country</motion.span>
        </h2>
        <motion.p variants={rise}>
          Countries group their companies, contacts, CVs, applications, interviews and follow-ups.
        </motion.p>
        <motion.button
          variants={rise}
          whileHover={reduced ? undefined : { y: -2, scale: 1.015 }}
          whileTap={reduced ? undefined : { scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 420, damping: 28 }}
          className="primary"
          onClick={() => add('countries')}
        >
          <span>Add country</span>
          <i aria-hidden="true">↗</i>
        </motion.button>
        <div className="welcome-mountains" aria-hidden="true">
          <i />
          <i />
          <i />
        </div>
      </motion.div>
    </motion.div>
  );
}

export function Dashboard({ data, scope, open, add, navigate, toggleFollowup }) {
  const apps = scope.applications;
  const due = scope.followups
    .filter((f) => !f.completed)
    .sort((a, b) => a.due_date.localeCompare(b.due_date));
  const upcoming = scope.interviews
    .filter((i) => i.status === 'Scheduled' && new Date(i.scheduled_at) >= new Date())
    .sort((a, b) => a.scheduled_at.localeCompare(b.scheduled_at));
  const summary = stats(data, apps);
  if (!data.countries.length) return <Welcome add={add} />;
  return (
    <>
      <motion.div className="metrics" variants={stagger} initial="hidden" animate="visible">
        {[
          [
            'applications',
            'Active applications',
            apps.filter((a) => !terminal.includes(a.status)).length,
            'Across your selected countries',
          ],
          [
            'followups',
            'Follow-ups due',
            due.filter((f) => f.due_date <= today()).length,
            'Due today or overdue',
          ],
          ['interviews', 'Upcoming interviews', upcoming.length, 'Scheduled in the future'],
          ['resumes', 'CV versions', scope.resumes.length, 'Originals and saved revisions'],
        ].map(([icon, title, value, sub]) => (
          <motion.div className="metric" key={title} variants={rise}>
            <Icon name={icon} />
            <span>{title}</span>
            <AnimatedNumber value={value} />
            <small>{sub}</small>
          </motion.div>
        ))}
      </motion.div>
      <div className="dashboard-grid">
        <Section
          title="Your application pipeline"
          action={
            <button className="text-button" onClick={() => navigate('applications')}>
              View applications →
            </button>
          }
        >
          <div className="funnel">
            {['Saved', 'Applied', 'Screening', 'Technical interview', 'Offer'].map((s, i) => {
              const count = apps.filter((a) => a.status === s).length;
              return (
                <div key={s}>
                  <strong>{count}</strong>
                  <div className="funnel-track">
                    <motion.div
                      initial={{ height: 0, opacity: 0.5 }}
                      animate={{
                        height: `${apps.length ? Math.max(3, (count / apps.length) * 100) : 0}%`,
                        opacity: 1,
                      }}
                      transition={{ duration: 0.75, delay: 0.12 + i * 0.07, ease: easeOut }}
                      style={{
                        background: `var(--stage-${i})`,
                      }}
                    />
                  </div>
                  <span>{s}</span>
                </div>
              );
            })}
          </div>
          <p className="caption">Current stages · other stages remain visible in Applications</p>
        </Section>
        <Section
          title="Next steps"
          action={
            <button className="text-button" onClick={() => add('followups')}>
              ＋ Follow-up
            </button>
          }
        >
          {due.slice(0, 5).map((f) => (
            <div className="task-row" key={f.id}>
              <input
                type="checkbox"
                aria-label={`Complete ${f.title}`}
                checked={false}
                onChange={() => toggleFollowup(f)}
              />
              <button className="row-link" onClick={() => open('followups', f.id)}>
                {f.title}
                <small>{dateLabel(f.due_date)}</small>
              </button>
              <Badge>
                {f.due_date < today() ? 'Overdue' : f.due_date === today() ? 'Today' : 'Upcoming'}
              </Badge>
            </div>
          ))}
          {!due.length && <p className="quiet-state">No open follow-ups.</p>}
        </Section>
        <Section
          title="Countries"
          action={
            <button className="text-button" onClick={() => navigate('countries')}>
              Explore →
            </button>
          }
        >
          {scope.countries.map((c) => {
            const count = scope.companies.filter((x) => x.country_id === c.id).length;
            return (
              <button key={c.id} className="country-row" onClick={() => open('countries', c.id)}>
                <span className="country-flag">{flag(c.code)}</span>
                <span>
                  <b>{c.name}</b>
                  <small>
                    {count} {count === 1 ? 'company' : 'companies'}
                  </small>
                </span>
                <Badge>{c.priority}</Badge>
                <span>↗</span>
              </button>
            );
          })}
        </Section>
        <Section
          title="Recent applications"
          action={
            <button className="text-button" onClick={() => add('applications')}>
              ＋ Application
            </button>
          }
        >
          {apps.slice(0, 5).map((a) => (
            <button className="record-row" key={a.id} onClick={() => open('applications', a.id)}>
              <span className="initial">
                {data.companies.find((c) => c.id === a.company_id)?.name[0]}
              </span>
              <span>
                <b>{a.title}</b>
                <small>{data.companies.find((c) => c.id === a.company_id)?.name}</small>
              </span>
              <Badge>{a.status}</Badge>
            </button>
          ))}
          {!apps.length && <p className="quiet-state">No applications yet.</p>}
        </Section>
        <Section title="Upcoming interviews">
          {upcoming.slice(0, 4).map((i) => (
            <button key={i.id} className="record-row" onClick={() => open('interviews', i.id)}>
              <span>
                <b>{i.title}</b>
                <small>
                  {dateLabel(i.scheduled_at)} ·{' '}
                  {new Date(i.scheduled_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </small>
              </span>
              <span>{i.duration_minutes} min</span>
            </button>
          ))}
          {!upcoming.length && <p className="quiet-state">No upcoming interviews scheduled.</p>}
        </Section>
        <Section title="Response rate">
          <div className="big-stat">{summary.rate}</div>
          <p>
            {summary.replied} recorded responses / {summary.submitted} submitted applications
          </p>
          <p className="caption">
            Record the first response date or log a “Reply received” interaction linked to an
            application.
          </p>
        </Section>
      </div>
    </>
  );
}

export function Analytics({ data, scope }) {
  const summary = stats(data, scope.applications);
  return (
    <>
      <p className="page-description">
        Calculated from saved applications, responses, interviews and status history.
      </p>
      <div className="metrics">
        {[
          ['Submitted', summary.submitted],
          ['Responses', summary.replied],
          ['Interviewed', summary.interviewed],
          ['Offers received', summary.offered],
        ].map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="dashboard-grid analytics-grid">
        {[
          [
            'By country',
            scope.countries.map((c) => [
              c.name,
              scope.applications.filter(
                (a) => data.companies.find((x) => x.id === a.company_id)?.country_id === c.id,
              ),
            ]),
          ],
          [
            'By CV version',
            scope.resumes.map((cv) => [
              `${cv.name} · v${cv.version}`,
              scope.applications.filter((a) => a.resume_id === cv.id),
            ]),
          ],
          [
            'By source',
            [...new Set(scope.applications.map((a) => a.source || 'Unspecified'))].map((source) => [
              source,
              scope.applications.filter((a) => (a.source || 'Unspecified') === source),
            ]),
          ],
        ].map(([title, groups]) => (
          <Section title={title} key={title}>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Group</th>
                    <th>Submitted</th>
                    <th>Replies</th>
                    <th>Response rate</th>
                  </tr>
                </thead>
                <tbody>
                  {groups.map(([name, apps]) => {
                    const s = stats(data, apps);
                    return (
                      <tr key={name}>
                        <td>{name}</td>
                        <td>{s.submitted}</td>
                        <td>{s.replied}</td>
                        <td>{s.rate}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {!groups.length && <p className="quiet-state">No records yet.</p>}
          </Section>
        ))}
      </div>
      <p className="caption">
        Small samples are directional, not proof that a CV or country performs better. Interviewed
        means at least one non-cancelled interview record. Offers count applications that reached
        Offer or Accepted at any time.
      </p>
    </>
  );
}
