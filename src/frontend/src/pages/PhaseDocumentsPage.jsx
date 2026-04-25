import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  CreditCard,
  FileText,
  Trophy,
  Landmark,
  Briefcase,
  GraduationCap,
  Clock,
  CalendarDays,
  Download,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTrackedItems } from '../hooks/useTrackedItems';
import OrgLogoCircle from '../components/OrgLogoCircle';
import TrackControl from '../components/TrackControl';

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] } },
};

const listVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

const chipBaseStyle = {
  fontSize: '0.72rem',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.25rem',
  padding: '0.15rem 0.5rem',
  borderRadius: '9999px',
};

const chipTheme = {
  neutral: { color: '#64748b', fontWeight: 500, background: '#f8fafc', border: '1px solid #e2e8f0' },
  info: { color: '#0369a1', fontWeight: 600, background: '#e0f2fe', border: '1px solid #bae6fd' },
  warning: { color: '#b45309', fontWeight: 600, background: '#fef3c7', border: '1px solid #fde68a' },
  success: { color: '#15803d', fontWeight: 600, background: '#dcfce7', border: '1px solid #bbf7d0' },
  link: { color: '#1d4ed8', fontWeight: 600, background: '#eff6ff', border: '1px solid #bfdbfe', textDecoration: 'none' },
};

function buildChip({ key, icon: Icon, text, theme = 'neutral', extraStyle = {} }) {
  return (
    <span key={key} style={{ ...chipBaseStyle, ...chipTheme[theme], ...extraStyle }}>
      {Icon ? <Icon size={10} strokeWidth={2} /> : null}
      {text}
    </span>
  );
}

function buildLinkChip({ key, icon: Icon, text, href }) {
  return (
    <a
      key={key}
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      style={{ ...chipBaseStyle, ...chipTheme.link }}
    >
      {Icon ? <Icon size={10} strokeWidth={2} /> : null}
      {text}
    </a>
  );
}

const PAGE_CONFIG = {
  'admit-cards': {
    endpoint: '/admit-cards',
    routeBase: 'admit-cards',
    badge: 'Admit Cards',
    title: 'Admit Cards',
    description: 'Download hall tickets and admit cards for upcoming examinations',
    badgeIcon: CreditCard,
    heroGradient: 'linear-gradient(135deg, #1e3a8a 0%, #1e40af 50%, #3b82f6 100%)',
    heroShadow: '0 16px 48px rgba(30,64,175,.4), 0 4px 12px rgba(30,64,175,.2)',
    cardLeftColor: '#2563eb',
    hoverBorderColor: '#93c5fd',
    logoGradient: 'linear-gradient(135deg,#1e3a5f,#3b82f6)',
    emptyMessage: 'No admit cards available.',
    skeletonChipWidths: [100, 110, 110],
    renderMeta: (item) => {
      const chips = [];
      if (item.published_at) {
        chips.push(buildChip({ key: 'published', icon: CalendarDays, text: `Published: ${item.published_at.slice(0, 10)}` }));
      }
      if (item.exam_start) {
        chips.push(buildChip({ key: 'exam-start', icon: Clock, text: `Exam From: ${item.exam_start}`, theme: 'info' }));
      }
      if (item.exam_end) {
        chips.push(buildChip({ key: 'exam-end', icon: Clock, text: `Exam Till: ${item.exam_end}`, theme: 'warning' }));
      }
      if (item.links?.length > 0 && item.links[0]?.url) {
        chips.push(buildLinkChip({ key: 'download', icon: Download, text: item.links[0].text || 'Download', href: item.links[0].url }));
      }
      return chips;
    },
  },
  'answer-keys': {
    endpoint: '/answer-keys',
    routeBase: 'answer-keys',
    badge: 'Answer Keys',
    title: 'Answer Keys',
    description: 'Official answer keys for government and entrance examinations',
    badgeIcon: FileText,
    heroGradient: 'linear-gradient(135deg, #78350f 0%, #92400e 45%, #d97706 100%)',
    heroShadow: '0 16px 48px rgba(146,64,14,.4), 0 4px 12px rgba(146,64,14,.2)',
    cardLeftColor: '#d97706',
    hoverBorderColor: '#fcd34d',
    logoGradient: 'linear-gradient(135deg,#78350f,#d97706)',
    emptyMessage: 'No answer keys available.',
    skeletonChipWidths: [100, 120, 115],
    renderMeta: (item) => {
      const chips = [];
      if (item.published_at) {
        chips.push(buildChip({ key: 'published', icon: CalendarDays, text: `Published: ${item.published_at.slice(0, 10)}` }));
      }
      if (item.start_date) {
        chips.push(buildChip({ key: 'challenge-start', icon: Clock, text: `Challenge From: ${item.start_date}`, theme: 'info' }));
      }
      if (item.end_date) {
        chips.push(buildChip({ key: 'challenge-end', icon: Clock, text: `Challenge Till: ${item.end_date}`, theme: 'warning' }));
      }
      return chips;
    },
  },
  results: {
    endpoint: '/results',
    routeBase: 'results',
    badge: 'Results',
    title: 'Results',
    description: 'Official results for government and entrance examinations',
    badgeIcon: Trophy,
    heroGradient: 'linear-gradient(135deg, #052e16 0%, #14532d 45%, #16a34a 100%)',
    heroShadow: '0 16px 48px rgba(20,83,45,.4), 0 4px 12px rgba(20,83,45,.2)',
    cardLeftColor: '#16a34a',
    hoverBorderColor: '#86efac',
    logoGradient: 'linear-gradient(135deg,#052e16,#16a34a)',
    emptyMessage: 'No results available.',
    skeletonChipWidths: [110, 160],
    renderMeta: (item) => {
      const chips = [];
      if (item.published_at) {
        chips.push(buildChip({ key: 'published', icon: CalendarDays, text: `Published: ${item.published_at.slice(0, 10)}`, theme: 'success' }));
      }
      if (item.notes) {
        chips.push(
          buildChip({
            key: 'notes',
            text: item.notes,
            extraStyle: { maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#475569' },
          }),
        );
      }
      return chips;
    },
  },
};

export default function PhaseDocumentsPage({ kind }) {
  const config = PAGE_CONFIG[kind];
  const navigate = useNavigate();
  const { token } = useAuth();

  const {
    items,
    pagination,
    loading,
    offset,
    limit,
    trackedJobIds,
    trackedAdmIds,
    track,
    setSearchParams,
  } = useTrackedItems(config.endpoint, token);

  const BadgeIcon = config.badgeIcon;

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        style={{
          background: config.heroGradient,
          color: '#fff',
          padding: '1.75rem 2rem',
          borderRadius: 'var(--radius-2xl)',
          marginBottom: '1.5rem',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: config.heroShadow,
        }}
      >
        <div style={{ position: 'absolute', top: -60, right: -40, width: 240, height: 240, background: 'rgba(255,255,255,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: -50, left: 20, width: 160, height: 160, background: 'rgba(255,255,255,.04)', borderRadius: '50%', pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(255,255,255,.14)', backdropFilter: 'blur(8px)', borderRadius: '0.5rem', padding: '0.28rem 0.75rem', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '0.75rem', border: '1px solid rgba(255,255,255,.1)' }}>
            <BadgeIcon size={11} strokeWidth={2.5} />
            {config.badge}
          </div>
          <h1 style={{ fontSize: '1.55rem', fontWeight: 800, marginBottom: '0.3rem', letterSpacing: '-0.025em', lineHeight: 1.18 }}>{config.title}</h1>
          <p style={{ fontSize: '0.875rem', opacity: 0.78, lineHeight: 1.6 }}>{config.description}</p>
        </div>
      </motion.div>

      {loading && ['s1', 's2', 's3', 's4', 's5'].map((sk) => (
        <div key={sk} style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: `3px solid ${config.cardLeftColor}`, borderRadius: '0.65rem', padding: '1rem 1.1rem', marginBottom: '0.65rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
            <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div className="skeleton" style={{ height: 15, width: '65%', borderRadius: '0.4rem', marginBottom: '0.4rem' }} />
              <div className="skeleton" style={{ height: 12, width: '50%', borderRadius: '0.4rem', marginBottom: '0.3rem' }} />
              <div className="skeleton" style={{ height: 11, width: '35%', borderRadius: '0.4rem' }} />
            </div>
          </div>
          <div style={{ borderTop: '1px solid #f1f5f9', marginTop: '0.55rem', paddingTop: '0.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              {config.skeletonChipWidths.map((width) => (
                <div key={`${sk}-${width}`} className="skeleton" style={{ height: 22, width, borderRadius: '9999px' }} />
              ))}
            </div>
            <div className="skeleton" style={{ height: 28, width: 88, borderRadius: '0.4rem' }} />
          </div>
        </div>
      ))}

      {!loading && items.length === 0 && <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>{config.emptyMessage}</div>}

      {!loading && (
        <motion.div variants={listVariants} initial="hidden" animate="show">
          {items.map((item) => {
            const parentType = item.job_id ? 'job' : 'admission';
            const trackId = item.job_id || item.admission_id;
            const isTracking = parentType === 'job' ? trackedJobIds.has(String(trackId)) : trackedAdmIds.has(String(trackId));
            const detailPath = `/${config.routeBase}/${item.slug}`;
            const meta = config.renderMeta(item);

            return (
              <motion.div
                key={item.id}
                variants={cardVariants}
                onClick={() => navigate(detailPath)}
                whileHover={{ y: -3, boxShadow: '0 8px 24px rgba(15,23,42,.1), 0 2px 8px rgba(15,23,42,.06)', borderColor: config.hoverBorderColor }}
                whileTap={{ scale: 0.99 }}
                style={{ background: '#fff', border: '1px solid #e2e8f0', borderLeft: `3px solid ${config.cardLeftColor}`, borderRadius: 'var(--radius-lg)', padding: '1rem 1.1rem', marginBottom: '0.65rem', boxShadow: 'var(--shadow-sm)', transition: 'border-color 0.15s', cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                  <OrgLogoCircle logoUrl={item.parent_logo_url} orgName={item.parent_organization} title={item.title} gradient={config.logoGradient} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h3 style={{ fontSize: '0.975rem', fontWeight: 700, lineHeight: 1.4, marginBottom: '0.15rem', color: '#0f172a' }}>{item.title}</h3>
                    {item.parent_title && (
                      <div style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.2rem' }}>
                        {item.parent_type === 'job' ? <Briefcase size={11} strokeWidth={2} /> : <GraduationCap size={11} strokeWidth={2} />}
                        {item.parent_title}
                      </div>
                    )}
                    {item.parent_organization && (
                      <div style={{ fontSize: '0.78rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Landmark size={10} strokeWidth={2} />
                        {item.parent_organization}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.55rem', paddingTop: '0.5rem', borderTop: '1px solid #f1f5f9', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', alignItems: 'center' }}>{meta}</div>
                  {trackId && (
                    <TrackControl
                      token={token}
                      isTracking={isTracking}
                      onTrack={() => track(parentType, trackId)}
                      loginPath={`/login?next=${detailPath}`}
                    />
                  )}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}

      {pagination.has_more && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <button onClick={() => setSearchParams({ offset: offset + limit })} className="btn btn-outline">Load More</button>
        </div>
      )}
    </div>
  );
}

PhaseDocumentsPage.propTypes = {
  kind: PropTypes.oneOf(['admit-cards', 'answer-keys', 'results']).isRequired,
};
