import { useState, useEffect, useRef } from 'react';
import {
  EmailAuthProvider,
  reauthenticateWithCredential,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth } from '../lib/firebase';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';

const STATES = ['Andhra Pradesh','Arunachal Pradesh','Assam','Bihar','Chhattisgarh','Goa','Gujarat','Haryana','Himachal Pradesh','Jharkhand','Karnataka','Kerala','Madhya Pradesh','Maharashtra','Manipur','Meghalaya','Mizoram','Nagaland','Odisha','Punjab','Rajasthan','Sikkim','Tamil Nadu','Telangana','Tripura','Uttar Pradesh','Uttarakhand','West Bengal','Delhi','Jammu & Kashmir','Ladakh'];
const CATEGORIES = ['general', 'obc', 'sc', 'st', 'ews'];
const CATEGORY_LABELS = { general: 'General', obc: 'OBC', sc: 'SC', st: 'ST', ews: 'EWS' };
const QUALIFICATIONS = [['10th','Class 10th'],['12th','Class 12th'],['diploma','Diploma'],['graduate','Graduate'],['postgraduate','Post Graduate'],['phd','PhD']];

function Modal({ title, open, onClose, children }) {
  if (!open) return null;
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: '0.5rem', padding: '1.5rem', maxWidth: 420, width: '100%' }}>
        <h3 style={{ margin: '0 0 1rem', color: '#1e3a5f' }}>{title}</h3>
        {children}
      </div>
    </div>
  );
}

const inputStyle = { width: '100%', padding: '0.5rem 0.75rem', border: '1.5px solid #e2e8f0', borderRadius: '0.4rem', fontSize: '0.875rem', color: '#1e293b', background: '#f8fafc' };
const labelStyle = { display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#374151', marginBottom: '0.3rem' };

export default function Profile() {
  const { token, logout } = useAuth();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [flash, setFlash] = useState({ type: '', msg: '' });
  const [tab, setTab] = useState('profile');

  // Firebase state
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [hasPassword, setHasPassword] = useState(false);
  const [hasEmail, setHasEmail] = useState(false);

  // Profile form
  const [gender, setGender] = useState('');
  const [state, setState] = useState('');
  const [city, setCity] = useState('');
  const [pincode, setPincode] = useState('');
  const [isPwd, setIsPwd] = useState(false);
  const [isExServiceman, setIsExServiceman] = useState(false);
  const [qualification, setQualification] = useState('');
  const [preferredStates, setPreferredStates] = useState('');
  const [preferredCategories, setPreferredCategories] = useState([]);

  // Notification prefs
  const [emailNotif, setEmailNotif] = useState(true);
  const [pushNotif, setPushNotif] = useState(false);

  // Phone modal
  const [phoneModal, setPhoneModal] = useState(false);
  const [newPhone, setNewPhone] = useState('');
  const [phoneVerifyModal, setPhoneVerifyModal] = useState(false);
  const [phoneVerifyStep, setPhoneVerifyStep] = useState('send'); // send | otp
  const [phoneOtp, setPhoneOtp] = useState('');
  const recaptchaRef = useRef(null);
  const recaptchaVerifier = useRef(null);
  const confirmResult = useRef(null);

  // Password modal
  const [pwdModal, setPwdModal] = useState(false);
  const [currentPwd, setCurrentPwd] = useState('');
  const [newPwd, setNewPwd] = useState('');
  const [confirmPwd, setConfirmPwd] = useState('');
  const [pwdError, setPwdError] = useState('');

  // Link email modal (phone-only users)
  const [linkEmailModal, setLinkEmailModal] = useState(false);
  const [linkEmail, setLinkEmail] = useState('');
  const [linkPwd, setLinkPwd] = useState('');
  const [linkConfirmPwd, setLinkConfirmPwd] = useState('');

  const showFlash = (type, msg) => { setFlash({ type, msg }); setTimeout(() => setFlash({ type: '', msg: '' }), 4000); };

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (fbUser) => {
      if (fbUser) {
        setFirebaseUser(fbUser);
        const providers = fbUser.providerData.map((p) => p.providerId);
        setHasPassword(providers.includes('password'));
        setHasEmail(Boolean(fbUser.email));
      }
    });
    return unsub;
  }, []);

  useEffect(() => {
    api.get('/users/profile').then((r) => {
      setUser(r.data);
      const p = r.data.profile || {};
      setProfile(p);
      setGender(p.gender || '');
      setState(p.state || '');
      setCity(p.city || '');
      setPincode(p.pincode || '');
      setIsPwd(p.is_pwd || false);
      setIsExServiceman(p.is_ex_serviceman || false);
      setQualification(p.highest_qualification || '');
      setPreferredStates((p.preferred_states || []).join(', '));
      setPreferredCategories(p.preferred_categories || []);
      const prefs = p.notification_preferences || {};
      setEmailNotif(prefs.email !== false);
      setPushNotif(prefs.push === true);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const saveProfile = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      await api.put('/users/profile', {
        gender: gender || null, state: state || null, city: city || null, pincode: pincode || null,
        is_pwd: isPwd, is_ex_serviceman: isExServiceman,
        highest_qualification: qualification || null,
        preferred_states: preferredStates.split(',').map((s) => s.trim()).filter(Boolean),
        preferred_categories: preferredCategories,
      });
      showFlash('success', 'Profile updated.');
    } catch (_) { showFlash('error', 'Failed to save profile.'); }
    finally { setSaving(false); }
  };

  const saveNotifPrefs = async (e) => {
    e.preventDefault();
    try {
      await api.put('/users/me/notification-preferences', { email: emailNotif, push: pushNotif });
      showFlash('success', 'Notification preferences saved.');
    } catch (_) { showFlash('error', 'Failed to save preferences.'); }
  };

  // ── Phone update ──────────────────────────────────────────────────────────

  const savePhone = async () => {
    if (!newPhone || !/^\+\d{10,15}$/.test(newPhone)) { showFlash('error', 'Enter a valid phone number (e.g. +91...)'); return; }
    try {
      await api.put('/users/profile/phone', { phone: newPhone });
      showFlash('success', 'Phone updated. Please verify it.');
      setPhoneModal(false);
      setUser((u) => ({ ...u, phone: newPhone, is_phone_verified: false }));
    } catch (e) { showFlash('error', e.response?.data?.detail || 'Failed to update phone.'); }
  };

  const startPhoneVerify = async () => {
    if (!user?.phone) return;
    setPhoneVerifyModal(true); setPhoneVerifyStep('send'); setPhoneOtp('');
  };

  const sendPhoneVerifyOtp = async () => {
    try {
      if (!recaptchaVerifier.current) {
        recaptchaVerifier.current = new RecaptchaVerifier(auth, recaptchaRef.current, { size: 'invisible' });
      }
      confirmResult.current = await signInWithPhoneNumber(auth, user.phone, recaptchaVerifier.current);
      setPhoneVerifyStep('otp');
    } catch (e) { showFlash('error', e.message || 'Failed to send code.'); }
  };

  const confirmPhoneOtp = async () => {
    if (!phoneOtp || phoneOtp.length !== 6) { showFlash('error', 'Enter the 6-digit code.'); return; }
    try {
      const cred = await confirmResult.current.confirm(phoneOtp);
      const idToken = await cred.user.getIdToken();
      await api.post('/auth/verify-token', { id_token: idToken });
      showFlash('success', 'Phone number verified!');
      setPhoneVerifyModal(false);
      setUser((u) => ({ ...u, is_phone_verified: true }));
    } catch (e) { showFlash('error', e.message || 'Verification failed.'); }
  };

  const closePhoneVerifyModal = () => {
    setPhoneVerifyModal(false);
    if (recaptchaVerifier.current) { try { recaptchaVerifier.current.clear(); } catch (_) {} recaptchaVerifier.current = null; }
  };

  // ── Password ──────────────────────────────────────────────────────────────

  const validate = (pwd) => {
    if (!pwd || pwd.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(pwd)) return 'Must contain at least one uppercase letter.';
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) return 'Must contain at least one special character.';
    return null;
  };

  const submitSetPassword = async () => {
    const err = validate(newPwd); if (err) { setPwdError(err); return; }
    if (newPwd !== confirmPwd) { setPwdError('Passwords do not match.'); return; }
    setPwdError('');
    try {
      await api.post('/users/me/set-password', { new_password: newPwd });
      showFlash('success', 'Password set! You can now sign in with email and password.');
      setHasPassword(true); setPwdModal(false); setNewPwd(''); setConfirmPwd('');
    } catch (e) { setPwdError(e.response?.data?.detail || 'Failed to set password.'); }
  };

  const submitChangePassword = async () => {
    if (!currentPwd) { setPwdError('Enter your current password.'); return; }
    const err = validate(newPwd); if (err) { setPwdError(err); return; }
    if (newPwd !== confirmPwd) { setPwdError('Passwords do not match.'); return; }
    setPwdError('');
    try {
      if (firebaseUser?.email) {
        const credential = EmailAuthProvider.credential(firebaseUser.email, currentPwd);
        await reauthenticateWithCredential(firebaseUser, credential);
      }
      await api.post('/users/me/change-password', { current_password: currentPwd, new_password: newPwd });
      showFlash('success', 'Password changed successfully.');
      setPwdModal(false); setCurrentPwd(''); setNewPwd(''); setConfirmPwd('');
    } catch (e) {
      if (e.code === 'auth/wrong-password' || e.code === 'auth/invalid-credential') setPwdError('Current password is incorrect.');
      else setPwdError(e.response?.data?.detail || e.message || 'Failed to change password.');
    }
  };

  // ── Link email+password (phone-only users) ────────────────────────────────

  const submitLinkEmail = async () => {
    if (!linkEmail) { showFlash('error', 'Enter an email address.'); return; }
    const err = validate(linkPwd); if (err) { showFlash('error', err); return; }
    if (linkPwd !== linkConfirmPwd) { showFlash('error', 'Passwords do not match.'); return; }
    try {
      await api.post('/users/me/link-email-password', { email: linkEmail, password: linkPwd });
      showFlash('success', 'Email and password added! You can now sign in with email/password.');
      setLinkEmailModal(false); setLinkEmail(''); setLinkPwd(''); setLinkConfirmPwd('');
      setHasEmail(true); setHasPassword(true);
    } catch (e) { showFlash('error', e.response?.data?.detail || 'Failed to link email.'); }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>Loading...</div>;

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%)', color: '#fff', padding: '1.5rem', borderRadius: '0.75rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ width: 60, height: 60, background: 'rgba(255,255,255,.2)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem', flexShrink: 0 }}>👤</div>
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{user?.full_name || 'User'}</div>
          <div style={{ fontSize: '0.85rem', opacity: 0.8 }}>{user?.email || user?.phone || ''}</div>
        </div>
      </div>

      {flash.msg && <div className={flash.type === 'success' ? 'flash-success' : 'flash-error'}>{flash.type === 'success' ? '✅' : '❌'} {flash.msg}</div>}

      {!profile?.gender && !profile?.highest_qualification && (
        <div style={{ background: '#fef3c7', border: '1px solid #fde68a', color: '#92400e', padding: '0.75rem 1rem', borderRadius: '0.375rem', marginBottom: '1.5rem', fontSize: '0.875rem' }}>
          Your profile hasn't been set up yet. Fill in the form below to get personalised recommendations.
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '1.5rem', overflowX: 'auto' }}>
        {[['profile', '👤 Profile'], ['notifications', '🔔 Notifications'], ['account', '🏦 Account'], ['security', '🔒 Security']].map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)} style={{ padding: '0.5rem 1rem', fontSize: '0.875rem', fontWeight: tab === t ? 700 : 500, cursor: 'pointer', background: 'none', border: 'none', borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent', marginBottom: -2, color: tab === t ? '#2563eb' : '#64748b', whiteSpace: 'nowrap' }}>
            {label}
          </button>
        ))}
      </div>

      {/* ── Profile tab ── */}
      {tab === 'profile' && (
        <form onSubmit={saveProfile}>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid #e2e8f0', color: '#1e3a5f' }}>Personal Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={labelStyle}>Full Name</label>
                <input value={user?.full_name || ''} disabled style={{ ...inputStyle, background: '#f1f5f9', color: '#64748b' }} />
              </div>
              <div>
                <label style={labelStyle}>Email</label>
                <input value={user?.email || ''} disabled style={{ ...inputStyle, background: '#f1f5f9', color: '#64748b' }} />
              </div>
              <div>
                <label style={labelStyle}>
                  Phone Number
                  {user?.phone && (
                    user?.is_phone_verified
                      ? <span style={{ marginLeft: '0.4rem', background: '#d1fae5', color: '#065f46', padding: '0.1rem 0.4rem', borderRadius: 9999, fontSize: '0.72rem', fontWeight: 600 }}>✓ Verified</span>
                      : <span style={{ marginLeft: '0.4rem', background: '#fee2e2', color: '#991b1b', padding: '0.1rem 0.4rem', borderRadius: 9999, fontSize: '0.72rem', fontWeight: 600 }}>⚠ Unverified</span>
                  )}
                </label>
                <input value={user?.phone || ''} disabled style={{ ...inputStyle, background: '#f1f5f9', color: '#64748b' }} placeholder="+91 98765 43210" />
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                  <button type="button" onClick={() => { setNewPhone(user?.phone || ''); setPhoneModal(true); }} className="btn btn-outline btn-sm">Edit Phone</button>
                  {user?.phone && !user?.is_phone_verified && (
                    <button type="button" onClick={startPhoneVerify} className="btn btn-primary btn-sm">Verify Now</button>
                  )}
                </div>
              </div>
              <div>
                <label style={labelStyle}>Gender</label>
                <select value={gender} onChange={(e) => setGender(e.target.value)} style={inputStyle}>
                  <option value="">— Select —</option>
                  {['Male', 'Female', 'Other'].map((g) => <option key={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>State</label>
                <select value={state} onChange={(e) => setState(e.target.value)} style={inputStyle}>
                  <option value="">— Select —</option>
                  {STATES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label style={labelStyle}>City</label>
                <input value={city} onChange={(e) => setCity(e.target.value)} style={inputStyle} placeholder="e.g. Lucknow" />
              </div>
              <div>
                <label style={labelStyle}>Pincode</label>
                <input value={pincode} onChange={(e) => setPincode(e.target.value)} style={inputStyle} placeholder="6-digit pincode" maxLength={6} />
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', cursor: 'pointer', padding: '0.3rem 0.6rem', border: '1px solid #e2e8f0', borderRadius: '0.375rem' }}>
                <input type="checkbox" checked={isPwd} onChange={(e) => setIsPwd(e.target.checked)} /> Person with Disability (PwD)
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', cursor: 'pointer', padding: '0.3rem 0.6rem', border: '1px solid #e2e8f0', borderRadius: '0.375rem' }}>
                <input type="checkbox" checked={isExServiceman} onChange={(e) => setIsExServiceman(e.target.checked)} /> Ex-Serviceman
              </label>
            </div>
          </div>

          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid #e2e8f0', color: '#1e3a5f' }}>
              Job Preferences <span style={{ fontSize: '0.8rem', fontWeight: 400, color: '#64748b' }}>— Used for personalised recommendations</span>
            </h3>
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={labelStyle}>Highest Qualification</label>
              <select value={qualification} onChange={(e) => setQualification(e.target.value)} style={inputStyle}>
                <option value="">— Select —</option>
                {QUALIFICATIONS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div style={{ marginBottom: '0.75rem' }}>
              <label style={labelStyle}>Preferred States <span style={{ color: '#94a3b8', fontWeight: 400 }}>(comma-separated)</span></label>
              <input value={preferredStates} onChange={(e) => setPreferredStates(e.target.value)} style={inputStyle} placeholder="Delhi, Uttar Pradesh, Bihar" />
            </div>
            <div>
              <label style={{ ...labelStyle, marginBottom: '0.4rem' }}>Preferred Categories</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {CATEGORIES.map((cat) => {
                  const active = preferredCategories.includes(cat);
                  return (
                    <label key={cat} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.85rem', cursor: 'pointer', background: active ? '#dbeafe' : '#f1f5f9', padding: '0.3rem 0.6rem', borderRadius: '0.375rem', border: `1px solid ${active ? '#bfdbfe' : '#e2e8f0'}` }}>
                      <input type="checkbox" checked={active} onChange={(e) => { if (e.target.checked) setPreferredCategories((p) => [...p, cat]); else setPreferredCategories((p) => p.filter((c) => c !== cat)); }} style={{ display: 'none' }} />
                      {CATEGORY_LABELS[cat]}
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          <button type="submit" disabled={saving} className="btn btn-primary" style={{ width: '100%', padding: '0.65rem' }}>
            {saving ? 'Saving...' : '💾 Save Profile'}
          </button>
        </form>
      )}

      {/* ── Notifications tab ── */}
      {tab === 'notifications' && (
        <form onSubmit={saveNotifPrefs}>
          <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1.5rem', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid #e2e8f0', color: '#1e3a5f' }}>Notification Preferences</h3>
            {[
              { state: emailNotif, setter: setEmailNotif, icon: '📧', label: 'Email Notifications', hint: 'Deadline reminders, new job alerts' },
              { state: pushNotif, setter: setPushNotif, icon: '🔔', label: 'Push Notifications', hint: 'Mobile app alerts (requires app)' },
            ].map(({ state: s, setter, icon, label, hint }) => (
              <label key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.75rem 1rem', background: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0', cursor: 'pointer', marginBottom: '0.5rem' }}>
                <div><div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{icon} {label}</div><div style={{ fontSize: '0.78rem', color: '#64748b' }}>{hint}</div></div>
                <input type="checkbox" checked={s} onChange={(e) => setter(e.target.checked)} style={{ accentColor: '#2563eb', width: 18, height: 18, cursor: 'pointer' }} />
              </label>
            ))}
          </div>
          <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '0.65rem' }}>💾 Save Preferences</button>
        </form>
      )}

      {/* ── Account tab ── */}
      {tab === 'account' && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid #e2e8f0', color: '#1e3a5f' }}>Account Information</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid #f1f5f9' }}>
            <div>
              <div style={{ fontWeight: 500, color: '#334155' }}>Email Address</div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.15rem' }}>
                {hasEmail ? (user?.email || firebaseUser?.email || '') : 'No email linked. Add email to enable email/password login.'}
              </div>
            </div>
            {!hasEmail && (
              <button onClick={() => setLinkEmailModal(true)} className="btn btn-outline btn-sm">Add Email</button>
            )}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid #f1f5f9' }}>
            <div>
              <div style={{ fontWeight: 500, color: '#334155' }}>Sign-in Methods</div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.15rem' }}>
                {firebaseUser?.providerData.map((p) => p.providerId).join(', ') || 'Loading…'}
              </div>
            </div>
          </div>
          <div style={{ padding: '0.75rem 0' }}>
            <div style={{ fontWeight: 500, color: '#334155' }}>Sign Out</div>
            <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '0.15rem', marginBottom: '0.75rem' }}>Signing out removes your session from this device.</div>
            <button onClick={logout} className="btn btn-outline" style={{ borderColor: '#fecaca', color: '#dc2626', background: '#fef2f2' }}>Sign Out</button>
          </div>
        </div>
      )}

      {/* ── Security tab ── */}
      {tab === 'security' && (
        <div style={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.75rem', padding: '1.5rem' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid #e2e8f0', color: '#1e3a5f' }}>Password</h3>
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
            {hasPassword ? 'You can change your current password.' : 'Set a password to enable email/password sign-in.'}
          </p>
          <button onClick={() => { setPwdModal(true); setPwdError(''); setCurrentPwd(''); setNewPwd(''); setConfirmPwd(''); }} className="btn btn-outline">
            {hasPassword ? 'Change Password' : 'Set Password'}
          </button>
        </div>
      )}

      {/* ── Modals ── */}

      {/* Edit phone */}
      <Modal title="Edit Phone Number" open={phoneModal} onClose={() => setPhoneModal(false)}>
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>New Phone Number</label>
          <input type="tel" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} style={inputStyle} placeholder="+91 98765 43210" />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button onClick={() => setPhoneModal(false)} className="btn btn-outline">Cancel</button>
          <button onClick={savePhone} className="btn btn-primary">Save</button>
        </div>
      </Modal>

      {/* Verify phone */}
      <Modal title="Verify Phone Number" open={phoneVerifyModal} onClose={closePhoneVerifyModal}>
        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1rem' }}>
          We'll send a verification code to <strong>{user?.phone}</strong>
        </p>
        <div ref={recaptchaRef} />
        {phoneVerifyStep === 'send' && (
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button onClick={closePhoneVerifyModal} className="btn btn-outline">Cancel</button>
            <button onClick={sendPhoneVerifyOtp} className="btn btn-primary">Send Code</button>
          </div>
        )}
        {phoneVerifyStep === 'otp' && (
          <>
            <div style={{ marginBottom: '0.7rem' }}>
              <label style={labelStyle}>Enter 6-digit code</label>
              <input value={phoneOtp} onChange={(e) => setPhoneOtp(e.target.value)} style={{ ...inputStyle, textAlign: 'center', letterSpacing: '0.25em' }} maxLength={6} placeholder="000000" />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button onClick={closePhoneVerifyModal} className="btn btn-outline">Cancel</button>
              <button onClick={confirmPhoneOtp} className="btn btn-primary">Verify</button>
            </div>
          </>
        )}
      </Modal>

      {/* Set/Change password */}
      <Modal title={hasPassword ? 'Change Password' : 'Set Password'} open={pwdModal} onClose={() => setPwdModal(false)}>
        {pwdError && <div className="flash-error" style={{ marginBottom: '0.75rem' }}>{pwdError}</div>}
        {hasPassword && (
          <div style={{ marginBottom: '0.7rem' }}>
            <label style={labelStyle}>Current Password</label>
            <input type="password" value={currentPwd} onChange={(e) => setCurrentPwd(e.target.value)} style={inputStyle} placeholder="Enter current password" />
          </div>
        )}
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>New Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 8 chars, 1 uppercase, 1 special)</span></label>
          <input type="password" value={newPwd} onChange={(e) => setNewPwd(e.target.value)} style={inputStyle} placeholder="New password" />
        </div>
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>Confirm New Password</label>
          <input type="password" value={confirmPwd} onChange={(e) => setConfirmPwd(e.target.value)} style={inputStyle} placeholder="Re-enter password" />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button onClick={() => setPwdModal(false)} className="btn btn-outline">Cancel</button>
          <button onClick={hasPassword ? submitChangePassword : submitSetPassword} className="btn btn-primary">
            {hasPassword ? 'Change Password' : 'Set Password'}
          </button>
        </div>
      </Modal>

      {/* Link email+password */}
      <Modal title="Add Email & Password" open={linkEmailModal} onClose={() => setLinkEmailModal(false)}>
        <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1rem' }}>Link an email address to enable email/password login.</p>
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>Email Address</label>
          <input type="email" value={linkEmail} onChange={(e) => setLinkEmail(e.target.value)} style={inputStyle} placeholder="your@email.com" />
        </div>
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 8 chars, 1 uppercase, 1 special)</span></label>
          <input type="password" value={linkPwd} onChange={(e) => setLinkPwd(e.target.value)} style={inputStyle} placeholder="Choose a password" />
        </div>
        <div style={{ marginBottom: '0.7rem' }}>
          <label style={labelStyle}>Confirm Password</label>
          <input type="password" value={linkConfirmPwd} onChange={(e) => setLinkConfirmPwd(e.target.value)} style={inputStyle} placeholder="Re-enter password" />
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
          <button onClick={() => setLinkEmailModal(false)} className="btn btn-outline">Cancel</button>
          <button onClick={submitLinkEmail} className="btn btn-primary">Add Email & Password</button>
        </div>
      </Modal>
    </div>
  );
}
