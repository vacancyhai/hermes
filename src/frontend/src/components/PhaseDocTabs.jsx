import { useState } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { Folder } from 'lucide-react';

function DocItem({ item, currentSlug, linkPrefix, accentColor, borderColor, bgColor }) {
  const isCurrent = item.slug === currentSlug;

  return (
    <div style={{ border: `1px solid ${borderColor}`, background: bgColor, borderRadius: '0.5rem', padding: '0.8rem 1rem', marginBottom: '0.65rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', flexWrap: 'wrap' }}>
      <div>
        <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{item.title}</div>
        {(item.exam_start || item.exam_end) && (
          <div style={{ fontSize: '0.8rem', color: '#b45309' }}>Exam: {item.exam_start || '?'} – {item.exam_end || '?'}</div>
        )}
      </div>
      {isCurrent
        ? <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600, padding: '0.38rem 0.75rem' }}>Current</span>
        : <Link to={`/${linkPrefix}/${item.slug}`} style={{ background: accentColor, color: '#fff', padding: '0.38rem 0.75rem', borderRadius: '0.5rem', fontSize: '0.78rem', fontWeight: 600, textDecoration: 'none' }}>View →</Link>
      }
    </div>
  );
}
DocItem.propTypes = {
  item: PropTypes.object.isRequired,
  currentSlug: PropTypes.string.isRequired,
  linkPrefix: PropTypes.string.isRequired,
  accentColor: PropTypes.string.isRequired,
  borderColor: PropTypes.string.isRequired,
  bgColor: PropTypes.string.isRequired,
};

export default function PhaseDocTabs({ admitCards, answerKeys, results, currentSlug }) {
  const [docTab, setDocTab] = useState('admit');
  const hasAdmitCards = admitCards.length > 0;
  const hasAnswerKeys = answerKeys.length > 0;
  const hasResults = results.length > 0;

  if (!hasAdmitCards && !hasAnswerKeys && !hasResults) return null;

  return (
    <div className="detail-section">
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}><Folder size={16} strokeWidth={2} />Phase Documents</h2>
      <div className="doc-tabs-bar">
        {hasAdmitCards && <button className={`doc-tab-btn${docTab === 'admit' ? ' active' : ''}`} onClick={() => setDocTab('admit')}>Admit Cards ({admitCards.length})</button>}
        {hasAnswerKeys && <button className={`doc-tab-btn${docTab === 'answer' ? ' active' : ''}`} onClick={() => setDocTab('answer')}>Answer Keys ({answerKeys.length})</button>}
        {hasResults && <button className={`doc-tab-btn${docTab === 'result' ? ' active' : ''}`} onClick={() => setDocTab('result')}>Results ({results.length})</button>}
      </div>
      {docTab === 'admit' && hasAdmitCards && (
        <div style={{ paddingTop: '0.85rem' }}>
          {admitCards.map((c) => <DocItem key={c.id} item={c} currentSlug={currentSlug} linkPrefix="admit-cards" accentColor="#2563eb" borderColor="#bfdbfe" bgColor="#eff6ff" />)}
        </div>
      )}
      {docTab === 'answer' && hasAnswerKeys && (
        <div style={{ paddingTop: '0.85rem' }}>
          {answerKeys.map((k) => <DocItem key={k.id} item={k} currentSlug={currentSlug} linkPrefix="answer-keys" accentColor="#d97706" borderColor="#fde68a" bgColor="#fefce8" />)}
        </div>
      )}
      {docTab === 'result' && hasResults && (
        <div style={{ paddingTop: '0.85rem' }}>
          {results.map((r) => <DocItem key={r.id} item={r} currentSlug={currentSlug} linkPrefix="results" accentColor="#16a34a" borderColor="#bbf7d0" bgColor="#f0fdf4" />)}
        </div>
      )}
    </div>
  );
}

PhaseDocTabs.propTypes = {
  admitCards: PropTypes.array.isRequired,
  answerKeys: PropTypes.array.isRequired,
  results: PropTypes.array.isRequired,
  currentSlug: PropTypes.string.isRequired,
};
