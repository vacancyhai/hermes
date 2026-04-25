import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import {
  Landmark,
  Users,
  Link2,
  Download,
  BookOpen,
  Globe,
  CheckCircle,
  GraduationCap,
  Briefcase,
} from 'lucide-react';
import PhaseDocTabs from './PhaseDocTabs';
import PhaseCard from './PhaseCard';

const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.16, 1, 0.3, 1] } },
};

const JOB_FEE_LABELS = {
  general: 'General / UR',
  obc: 'OBC-NCL',
  sc_st: 'SC / ST',
  ews: 'EWS',
  female: 'Female / PwBD',
};

const JOB_LINK_STYLES = {
  apply_online: { background: '#2563eb', color: '#fff', borderColor: '#2563eb' },
  download_notification: { background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' },
  syllabus: { background: '#0891b2', color: '#fff', borderColor: '#0891b2' },
};

const JOB_LINK_ICONS = {
  apply_online: BookOpen,
  download_notification: Download,
  syllabus: BookOpen,
  official_website: Globe,
};

function SectionDivider({ icon: Icon, label }) {
  return (
    <div style={{ margin: '1.5rem 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'flex', alignItems: 'center', gap: '0.3rem', whiteSpace: 'nowrap' }}>
        <Icon size={12} strokeWidth={2} />
        {label}
      </span>
      <div style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
    </div>
  );
}

SectionDivider.propTypes = {
  icon: PropTypes.elementType.isRequired,
  label: PropTypes.string.isRequired,
};

function HeroPanel({ className, badge, title, subtitle, note, status }) {
  return (
    <div className={className} style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.75rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {badge && (
            <span style={{ background: 'rgba(255,255,255,.2)', color: '#fff', padding: '0.15rem 0.55rem', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 600, display: 'inline-block', marginBottom: '0.5rem' }}>
              {badge}
            </span>
          )}
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff', margin: 0 }}>{title}</h2>
          {subtitle}
          {note && <div style={{ marginTop: '0.35rem', fontSize: '0.875rem', opacity: 0.9 }}>{note}</div>}
        </div>
        {status && (
          <div>
            <span className={`status-pill status-${status}`}>{status.charAt(0).toUpperCase() + status.slice(1)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

HeroPanel.propTypes = {
  className: PropTypes.string.isRequired,
  badge: PropTypes.string,
  title: PropTypes.string.isRequired,
  subtitle: PropTypes.node,
  note: PropTypes.string,
  status: PropTypes.string,
};

function ActionBar({ sourceUrl, applyUrl, applyStyle }) {
  return (
    <div className="action-bar" style={{ marginBottom: '0.75rem' }}>
      {sourceUrl && (
        <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="share-btn" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
          <Globe size={13} strokeWidth={2} />Official Website
        </a>
      )}
      {applyUrl && (
        <a href={applyUrl} target="_blank" rel="noopener noreferrer" className="share-btn" style={applyStyle}>
          Apply Online →
        </a>
      )}
    </div>
  );
}

ActionBar.propTypes = {
  sourceUrl: PropTypes.string,
  applyUrl: PropTypes.string,
  applyStyle: PropTypes.object,
};

function DetailGrid({ rows, isActive }) {
  const visibleRows = rows.filter(([, value]) => value);

  return (
    <div className="detail-grid">
      {visibleRows.map(([label, value]) => (
        <div key={label} className="detail-item">
          <div className="label">{label}</div>
          <div className={`value${label === 'Last Date to Apply' && isActive ? ' urgent' : ''}`}>{value}</div>
        </div>
      ))}
    </div>
  );
}

DetailGrid.propTypes = {
  rows: PropTypes.arrayOf(PropTypes.array).isRequired,
  isActive: PropTypes.bool.isRequired,
};

function HtmlDescriptionSection({ title, html }) {
  if (!html) return null;

  return (
    <div className="detail-section">
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <BookOpen size={16} strokeWidth={2} />
        {title}
      </h2>
      <div dangerouslySetInnerHTML={{ __html: html }} style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.65 }} />
    </div>
  );
}

HtmlDescriptionSection.propTypes = {
  title: PropTypes.string.isRequired,
  html: PropTypes.string,
};

function EligibilitySection({ eligibility }) {
  if (!eligibility) return null;

  const hasData = eligibility.min_qualification || eligibility.age_limit || eligibility.qualification_details;
  if (!hasData) return null;

  const age = eligibility.age_limit;

  return (
    <div className="detail-section">
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <CheckCircle size={16} strokeWidth={2} />Eligibility Criteria
      </h2>
      {eligibility.min_qualification && <p><strong>Minimum Qualification:</strong> {eligibility.min_qualification}</p>}
      {age && (
        <p style={{ marginTop: '0.4rem' }}>
          <strong>Age Limit:</strong>{' '}
          {age.min && age.max ? `${age.min} – ${age.max} years` : ''}
          {age.cutoff_date ? ` (as on ${age.cutoff_date})` : ''}
        </p>
      )}
      {eligibility.qualification_details && <p style={{ marginTop: '0.4rem' }}>{eligibility.qualification_details}</p>}
    </div>
  );
}

EligibilitySection.propTypes = {
  eligibility: PropTypes.object,
};

function CountBadges({ values, keys, emphasizeFirst = false }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.5rem' }}>
      {keys.filter((key) => values[key]).map((key, index) => (
        <div key={key} style={{ background: emphasizeFirst && index === 0 ? '#dbeafe' : '#f1f5f9', borderRadius: '0.35rem', padding: '0.35rem 0.65rem', textAlign: 'center', minWidth: 54 }}>
          <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>{Number(values[key]).toLocaleString()}</div>
          <div style={{ fontSize: '0.66rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{key}</div>
        </div>
      ))}
    </div>
  );
}

CountBadges.propTypes = {
  values: PropTypes.object.isRequired,
  keys: PropTypes.arrayOf(PropTypes.string).isRequired,
  emphasizeFirst: PropTypes.bool,
};

function FeeSection({ fee, labels }) {
  if (!fee || Object.keys(fee).length === 0) return null;

  const orderedKeys = labels ? ['general', 'obc', 'sc_st', 'ews', 'female'].filter((key) => key in fee) : Object.keys(fee);

  return (
    <div className="detail-section">
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <CheckCircle size={16} strokeWidth={2} />Application Fee
      </h2>
      <table className="fee-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Fee</th>
          </tr>
        </thead>
        <tbody>
          {orderedKeys.map((key) => (
            <tr key={key}>
              <td>{labels?.[key] || key}</td>
              <td>{fee[key] === 0 ? 'Free' : `₹${fee[key]}`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

FeeSection.propTypes = {
  fee: PropTypes.object,
  labels: PropTypes.object,
};

function ImportantLinksSection({ links, styleMap = {}, iconMap = {} }) {
  const validLinks = links.filter((link) => (typeof link === 'object' ? link.url : link));
  if (validLinks.length === 0) return null;

  return (
    <div className="detail-section">
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
        <Link2 size={16} strokeWidth={2} />Important Links
      </h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {validLinks.map((link) => {
          const url = typeof link === 'object' ? link.url : link;
          const text = typeof link === 'object' ? (link.text || url) : url;
          const type = typeof link === 'object' ? (link.type || '') : '';
          const Icon = iconMap[type] || Link2;
          const baseStyle = { display: 'inline-flex', alignItems: 'center', gap: '0.35rem' };
          const linkStyle = styleMap[type] ? { ...styleMap[type], ...baseStyle } : baseStyle;
          return (
            <a key={url} href={url} target="_blank" rel="noopener noreferrer" className="share-btn" style={linkStyle}>
              <Icon size={13} strokeWidth={2} />
              {text}
            </a>
          );
        })}
      </div>
    </div>
  );
}

ImportantLinksSection.propTypes = {
  links: PropTypes.array.isRequired,
  styleMap: PropTypes.object,
  iconMap: PropTypes.object,
};

function JobParent({ job, currentSlug }) {
  const importantLinks = job.application_details?.important_links || [];
  const vacancyBreakdown = job.vacancy_breakdown || {};
  const vacancyPosts = vacancyBreakdown.posts || [];

  const detailRows = [
    ['Notification Date', job.notification_date],
    ['Apply From', job.application_start],
    ['Last Date to Apply', job.application_end],
    ['Exam Start', job.exam_start],
    ['Exam End', job.exam_end],
    ['Result Date', job.result_date],
  ];

  if (job.salary_initial) {
    const minSalary = `₹${job.salary_initial.toLocaleString()}`;
    const maxSalary = job.salary_max ? ` – ₹${job.salary_max.toLocaleString()}` : '';
    detailRows.push([
      'Pay Scale',
      `${minSalary}${maxSalary}`,
    ]);
  }

  return (
    <motion.div variants={fadeUp}>
      <SectionDivider icon={Briefcase} label="Related Job Details" />

      <HeroPanel
        className="detail-hero hero-job"
        badge={job.qualification_level}
        title={job.job_title}
        subtitle={(
          <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
            <Landmark size={14} strokeWidth={2} />
            {job.organization}
            {job.department && job.department !== job.organization ? ` · ${job.department}` : ''}
          </div>
        )}
        note={job.total_vacancies ? `${job.total_vacancies.toLocaleString()} vacancies` : ''}
        status={job.status}
      />

      <ActionBar
        sourceUrl={job.source_url}
        applyUrl={job.application_details?.application_link}
        applyStyle={{ background: '#2563eb', color: '#fff', borderColor: '#2563eb' }}
      />

      <DetailGrid rows={detailRows} isActive={job.status === 'active'} />

      <HtmlDescriptionSection title="About This Recruitment" html={job.description} />

      <EligibilitySection eligibility={job.eligibility} />

      {(vacancyBreakdown.total || vacancyBreakdown.UR || vacancyBreakdown.SC) && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Users size={16} strokeWidth={2} />Vacancy Breakdown
          </h2>
          <CountBadges values={vacancyBreakdown} keys={['total', 'UR', 'OBC', 'EWS', 'SC', 'ST', 'PWD', 'male', 'female']} emphasizeFirst />
        </div>
      )}

      {vacancyPosts.length > 0 && vacancyPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Users size={16} strokeWidth={2} />Posts &amp; Vacancies
          </h2>
          {vacancyPosts.map((post, index) => {
            const postVacancy = post.postwise_vacancy || {};

            return (
              <div key={post.post_name || index} style={{ border: '1px solid #e2e8f0', borderRadius: '0.5rem', marginBottom: '0.85rem', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.6rem 0.95rem', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', flexWrap: 'wrap', gap: '0.35rem' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>{post.post_name}</span>
                  {postVacancy.total && <span style={{ background: '#dbeafe', color: '#1e40af', fontSize: '0.78rem', fontWeight: 700, padding: '0.15rem 0.55rem', borderRadius: 9999 }}>{postVacancy.total.toLocaleString()} posts</span>}
                </div>
                <div style={{ padding: '0.75rem 0.95rem' }}>
                  {Object.keys(postVacancy).length > 0 && <CountBadges values={postVacancy} keys={['UR', 'OBC', 'EWS', 'SC', 'ST', 'PWD', 'male', 'female']} />}
                  {post.selection_process?.map((step, stepIndex) => (
                    <PhaseCard key={typeof step === 'object' ? (step.name || stepIndex) : stepIndex} step={step} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {vacancyPosts.length > 0 && !vacancyPosts[0]?.post_name && (
        <div className="detail-section">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <CheckCircle size={16} strokeWidth={2} />Selection Process
          </h2>
          {vacancyPosts.map((step, stepIndex) => (
            <PhaseCard key={typeof step === 'object' ? (step.name || stepIndex) : stepIndex} step={step} />
          ))}
        </div>
      )}

      <FeeSection fee={job.fee} labels={JOB_FEE_LABELS} />

      <ImportantLinksSection links={importantLinks} styleMap={JOB_LINK_STYLES} iconMap={JOB_LINK_ICONS} />

      <PhaseDocTabs admitCards={job.admit_cards || []} answerKeys={job.answer_keys || []} results={job.results || []} currentSlug={currentSlug} />
    </motion.div>
  );
}

JobParent.propTypes = {
  job: PropTypes.object.isRequired,
  currentSlug: PropTypes.string.isRequired,
};

function AdmissionParent({ admission, currentSlug }) {
  const importantLinks = admission.admission_details?.important_links || [];

  const detailRows = [
    ['Apply From', admission.application_start],
    ['Last Date to Apply', admission.application_end],
    ['Exam Start', admission.exam_start],
    ['Exam End', admission.exam_end],
    ['Counselling Start', admission.counselling_start],
    ['Result Date', admission.result_date],
  ];

  return (
    <motion.div variants={fadeUp}>
      <SectionDivider icon={GraduationCap} label="Related Admission Details" />

      <HeroPanel
        className="detail-hero hero-admission"
        badge={admission.stream}
        title={admission.admission_name}
        subtitle={(
          <div style={{ fontSize: '0.875rem', opacity: 0.88, display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.25rem' }}>
            <Landmark size={14} strokeWidth={2} />
            {admission.conducting_body}
          </div>
        )}
        status={admission.status}
      />

      <ActionBar
        sourceUrl={admission.source_url}
        applyUrl={admission.admission_details?.application_link}
        applyStyle={{ background: '#7c3aed', color: '#fff', borderColor: '#7c3aed' }}
      />

      <DetailGrid rows={detailRows} isActive={admission.status === 'active'} />

      <HtmlDescriptionSection title="About This Admission" html={admission.description} />

      <EligibilitySection eligibility={admission.eligibility} />

      <FeeSection fee={admission.fee} />

      <ImportantLinksSection links={importantLinks} />

      <PhaseDocTabs admitCards={admission.admit_cards || []} answerKeys={admission.answer_keys || []} results={admission.results || []} currentSlug={currentSlug} />
    </motion.div>
  );
}

AdmissionParent.propTypes = {
  admission: PropTypes.object.isRequired,
  currentSlug: PropTypes.string.isRequired,
};

export default function ParentDetail(props) {
  const { type, data, currentSlug } = props;

  if (type === 'job') return <JobParent job={data} currentSlug={currentSlug} />;
  if (type === 'admission') return <AdmissionParent admission={data} currentSlug={currentSlug} />;
  return null;
}

ParentDetail.propTypes = {
  type: PropTypes.oneOf(['job', 'admission']).isRequired,
  data: PropTypes.object.isRequired,
  currentSlug: PropTypes.string.isRequired,
};
