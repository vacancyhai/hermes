import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Landmark, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import {
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  signInWithCustomToken,
  signInWithPhoneNumber,
  RecaptchaVerifier,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { auth } from '../lib/firebase';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';

function firebaseErr(e) {
  const map = {
    'auth/user-not-found': 'No account found with this email.',
    'auth/wrong-password': 'Incorrect password.', // pragma: allowlist secret
    'auth/invalid-credential': 'Invalid email or password.',
    'auth/email-already-in-use': 'An account with this email already exists.',
    'auth/weak-password': 'Password must be at least 6 characters.', // pragma: allowlist secret
    'auth/invalid-email': 'Please enter a valid email address.',
    'auth/too-many-requests': 'Too many attempts. Please try again later.',
    'auth/popup-closed-by-user': 'Google sign-in was cancelled.',
    'auth/invalid-phone-number': 'Please enter a valid phone number (e.g. +91...).',
    'auth/invalid-verification-code': 'Invalid OTP code. Please try again.',
    'auth/code-expired': 'OTP expired. Please request a new one.',
  };
  return map[e.code] || e.message || 'Something went wrong.';
}

const FIREBASE_API_KEY = import.meta.env.VITE_FIREBASE_API_KEY || '';

export default function Login() {
  const { login, token } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const nextUrl = new URLSearchParams(location.search).get('next') || '/';
  const [tab, setTab] = useState('email');
  const [emailView, setEmailView] = useState('signin'); // signin | register | otp | addpwd | addpwd-otp
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [addPwd, setAddPwd] = useState('');
  const [addPwdOtp, setAddPwdOtp] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneOtp, setPhoneOtp] = useState('');
  const [phoneStep, setPhoneStep] = useState('input'); // input | otp
  const [showPw, setShowPw] = useState(false);
  const [showRegPw, setShowRegPw] = useState(false);

  const regState = useRef({});
  const addPwdState = useRef({});
  const confirmResult = useRef(null);
  const recaptchaRef = useRef(null);
  const recaptchaVerifier = useRef(null);

  useEffect(() => { if (token) navigate(nextUrl, { replace: true }); }, [token]);

  const clearMsg = () => { setError(''); setSuccess(''); };

  async function sendTokenToServer(idToken, fullName) {
    const res = await api.post('/auth/verify-token', { id_token: idToken, full_name: fullName || null });
    const { access_token, refresh_token } = res.data;
    let name = fullName || '';
    try {
      const me = await api.get('/users/profile', { headers: { Authorization: `Bearer ${access_token}` } });
      name = me.data.full_name || name;
    } catch { }
    login(access_token, refresh_token, name);
    navigate(nextUrl, { replace: true });
  }

  async function loginWithGoogle() {
    if (!FIREBASE_API_KEY) { setError('Firebase not configured.'); return; }
    clearMsg(); setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const cred = await signInWithPopup(auth, provider);
      const idToken = await cred.user.getIdToken();
      await sendTokenToServer(idToken, cred.user.displayName);
    } catch (e) {
      setError(firebaseErr(e));
    } finally { setLoading(false); }
  }

  async function loginWithEmail() {
    if (!FIREBASE_API_KEY) return;
    if (!email || !password) { setError('Please enter email and password.'); return; }
    clearMsg(); setLoading(true);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const idToken = await cred.user.getIdToken();
      await sendTokenToServer(idToken);
    } catch (e) {
      if (e.code === 'auth/wrong-password' || e.code === 'auth/user-not-found' || e.code === 'auth/invalid-credential') {
        try {
          const r = await api.post('/auth/check-user-providers', { email });
          const data = r.data;
          if (!data.exists) { setError('No account found with this email.'); }
          else if (data.can_add_password && data.providers?.includes('google')) {
            setError('You signed up with Google. Please sign in with Google or add a password.');
            setTimeout(() => { addPwdState.current.email = email; addPwdState.current.password = password; setEmailView('addpwd'); setAddPwd(password); }, 1500);
          } else { setError('Incorrect password.'); }
        } catch { setError('Invalid email or password.'); }
      } else { setError(firebaseErr(e)); }
    } finally { setLoading(false); }
  }

  async function registerWithEmail() {
    if (!regName || !regEmail || !regPassword) { setError('Please fill in all required fields.'); return; }
    if (regPassword.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (!/[A-Z]/.test(regPassword)) { setError('Password must contain at least one uppercase letter.'); return; }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(regPassword)) { setError('Password must contain at least one special character.'); return; }
    if (regPhone && !/^\+\d{10,15}$/.test(regPhone)) { setError('Phone must be in format +91...'); return; }
    clearMsg(); setLoading(true);
    regState.current = { email: regEmail, password: regPassword, name: regName, phone: regPhone || null };
    try {
      const body = { email: regEmail, full_name: regName };
      if (regPhone) body.phone = regPhone;
      await api.post('/auth/send-email-otp', body);
      setEmailView('otp');
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to send verification email.');
    } finally { setLoading(false); }
  }

  async function verifyEmailOTP() {
    if (otpCode?.length !== 6) { setError('Please enter the 6-digit code.'); return; }
    const { email: re, password: rp, name: rn, phone: rph } = regState.current;
    if (!re || !rp) { setError('Session expired. Please register again.'); setEmailView('register'); return; }
    clearMsg(); setLoading(true);
    try {
      const v = await api.post('/auth/verify-email-otp', { email: re, otp: otpCode });
      if (!v.data.verified) throw new Error(v.data.error || 'Invalid code.');
      const body = { email: re, password: rp, verification_token: v.data.verification_token };
      if (rph) body.phone = rph;
      const reg = await api.post('/auth/complete-registration', body);
      if (!reg.data.custom_token) throw new Error(reg.data.error || 'Failed to create account.');
      const cred = await signInWithCustomToken(auth, reg.data.custom_token);
      const idToken = await cred.user.getIdToken();
      await sendTokenToServer(idToken, rn);
    } catch (e) {
      setError(e.message || 'Verification failed.');
    } finally { setLoading(false); }
  }

  async function resendEmailOTP() {
    const { email: re, name: rn } = regState.current;
    if (!re || !rn) { setError('Session expired.'); setEmailView('register'); return; }
    clearMsg();
    try {
      await api.post('/auth/send-email-otp', { email: re, full_name: rn });
      setSuccess('A new code has been sent to your email.'); setOtpCode('');
    } catch { setError('Failed to resend code.'); }
  }

  async function requestAddPassword() {
    if (!addPwd || addPwd.length < 6) { setError('Password must be at least 6 characters.'); return; }
    const em = addPwdState.current.email;
    if (!em) { setError('Session expired.'); setEmailView('signin'); return; }
    clearMsg(); setLoading(true);
    addPwdState.current.password = addPwd;
    try {
      await api.post('/auth/send-email-otp', { email: em, full_name: 'User' });
      setEmailView('addpwd-otp');
    } catch { setError('Failed to send verification code.'); }
    finally { setLoading(false); }
  }

  async function verifyAndAddPassword() {
    if (addPwdOtp?.length !== 6) { setError('Please enter the 6-digit code.'); return; }
    const { email: em, password: pw } = addPwdState.current;
    if (!em || !pw) { setError('Session expired.'); setEmailView('signin'); return; }
    clearMsg(); setLoading(true);
    try {
      const v = await api.post('/auth/verify-email-otp', { email: em, otp: addPwdOtp });
      if (!v.data.verified) throw new Error(v.data.error || 'Invalid code.');
      const r = await api.post('/auth/add-password', { email: em, password: pw, verification_token: v.data.verification_token });
      if (!r.data.custom_token) throw new Error(r.data.error || 'Failed to add password.');
      const cred = await signInWithCustomToken(auth, r.data.custom_token);
      const idToken = await cred.user.getIdToken();
      await sendTokenToServer(idToken);
    } catch (e) { setError(e.message || 'Failed to add password.');
    } finally { setLoading(false); }
  }

  async function forgotPassword() {
    if (!email) { setError('Please enter your email first.'); return; }
    clearMsg();
    try { await sendPasswordResetEmail(auth, email); setSuccess('Password reset email sent. Check your inbox.'); }
    catch (e) { setError(firebaseErr(e)); }
  }

  async function sendPhoneOTP() {
    if (!phoneNumber) { setError('Please enter phone number.'); return; }
    if (!auth) return;
    clearMsg(); setLoading(true);
    try {
      if (!recaptchaVerifier.current) {
        recaptchaVerifier.current = new RecaptchaVerifier(auth, recaptchaRef.current, { size: 'invisible' });
      }
      confirmResult.current = await signInWithPhoneNumber(auth, phoneNumber, recaptchaVerifier.current);
      setPhoneStep('otp');
    } catch (e) { setError(firebaseErr(e)); }
    finally { setLoading(false); }
  }

  async function verifyPhoneOTP() {
    if (!phoneOtp || phoneOtp.length < 4) { setError('Enter the OTP.'); return; }
    if (!confirmResult.current) { setError('Session expired.'); setPhoneStep('input'); return; }
    clearMsg(); setLoading(true);
    try {
      const cred = await confirmResult.current.confirm(phoneOtp);
      const idToken = await cred.user.getIdToken();
      await sendTokenToServer(idToken);
    } catch (e) { setError(firebaseErr(e)); }
    finally { setLoading(false); }
  }

  const inputStyle = {
    width: '100%', padding: '0.55rem 0.85rem',
    border: '1.5px solid #e2e8f0', borderRadius: 'var(--radius)',
    fontSize: '0.875rem', color: '#1e293b',
    background: '#f8fafc', outline: 'none',
    transition: 'border-color 0.15s, box-shadow 0.15s',
    fontFamily: 'inherit',
  };
  const labelStyle = { display: 'block', fontSize: '0.75rem', fontWeight: 700, color: '#374151', marginBottom: '0.3rem', letterSpacing: '0.01em' };
  const fieldWrap = { marginBottom: '0.85rem' };
  const primaryBtn = { width: '100%', padding: '0.6rem', borderRadius: 'var(--radius)', background: 'linear-gradient(135deg, #1e3a5f 0%, #1d4ed8 60%, #3b82f6 100%)', color: '#fff', fontSize: '0.875rem', fontWeight: 700, border: 'none', cursor: 'pointer', boxShadow: '0 4px 16px rgba(37,99,235,.35)', letterSpacing: '0.01em', transition: 'box-shadow 0.2s, filter 0.15s' };
  const greenBtn  = { ...primaryBtn, background: 'linear-gradient(135deg, #065f46 0%, #059669 60%, #10b981 100%)', boxShadow: '0 4px 16px rgba(5,150,105,.35)' };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '1.5rem 1rem', minHeight: '80vh' }}>
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        style={{ display: 'flex', width: '100%', maxWidth: 880, borderRadius: 'var(--radius-2xl)', overflow: 'hidden', boxShadow: '0 32px 80px rgba(0,0,0,.22), 0 8px 24px rgba(0,0,0,.12)' }}
      >
        {/* Left branding panel */}
        <div style={{ flex: '0 0 300px', background: 'linear-gradient(160deg, #0a1628 0%, #0f2440 30%, #1e3a5f 65%, #2563eb 100%)', padding: '2.5rem 2rem', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: '#fff', position: 'relative', overflow: 'hidden' }} className="login-brand-panel">
          {/* decorative circles */}
          <div style={{ position: 'absolute', top: -80, right: -80, width: 260, height: 260, background: 'rgba(255,255,255,.05)', borderRadius: '50%', pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: -100, left: -60, width: 240, height: 240, background: 'rgba(99,162,251,.06)', borderRadius: '50%', pointerEvents: 'none' }} />
          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ width: 52, height: 52, background: 'linear-gradient(135deg, rgba(255,255,255,.18), rgba(255,255,255,.08))', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,.15)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 4px 16px rgba(0,0,0,.2)' }}>
              <Landmark size={26} strokeWidth={2} />
            </div>
            <h1 style={{ fontSize: '1.55rem', fontWeight: 800, marginBottom: '0.5rem', letterSpacing: '-0.025em' }}>Vacancy Hai</h1>
            <p style={{ fontSize: '0.85rem', opacity: 0.75, lineHeight: 1.65, marginBottom: '2rem' }}>Your one-stop platform for government jobs &amp; admission notifications.</p>
            {['Latest central &amp; state govt jobs', 'NEET, JEE, GATE, CAT &amp; more', 'Admit cards, answer keys &amp; results', 'Personalised job &amp; admission alerts'].map((f) => (
              <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.82rem', marginBottom: '0.85rem' }}>
                <span style={{ width: 18, height: 18, borderRadius: '50%', background: 'rgba(96,165,250,.2)', border: '1px solid rgba(96,165,250,.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <CheckCircle2 size={11} strokeWidth={2.5} color="#93c5fd" />
                </span>
                <span style={{ opacity: 0.88 }} dangerouslySetInnerHTML={{ __html: f }} />
              </div>
            ))}
          </div>
        </div>

        {/* Right form */}
        <div style={{ flex: 1, background: '#fff', padding: '2rem 2rem', overflowY: 'auto', maxHeight: '92vh' }}>
          <div style={{ maxWidth: 340, margin: '0 auto' }}>

            {!FIREBASE_API_KEY && <div className="flash-error" style={{ marginBottom: '1rem', fontSize: '0.8rem' }}>Firebase not configured. Contact administrator.</div>}
            {error && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="flash-error" style={{ marginBottom: '0.75rem', fontSize: '0.82rem' }}>{error}</motion.div>
            )}
            {success && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} className="flash-success" style={{ marginBottom: '0.75rem', fontSize: '0.82rem' }}>{success}</motion.div>
            )}

            {/* Google */}
            <motion.button
              whileHover={{ y: -2, boxShadow: '0 6px 20px rgba(0,0,0,.1)' }}
              whileTap={{ scale: 0.98 }}
              onClick={loginWithGoogle} disabled={loading}
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem', width: '100%', padding: '0.6rem', border: '1.5px solid #e2e8f0', borderRadius: 'var(--radius)', background: '#fff', fontSize: '0.84rem', cursor: 'pointer', fontWeight: 600, color: '#334155', boxShadow: 'var(--shadow-xs)', transition: 'border-color 0.15s' }}
            >
              <svg viewBox="0 0 24 24" width={16} height={16}><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Sign in with Google
            </motion.button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', margin: '1rem 0', color: '#94a3b8', fontSize: '0.75rem', fontWeight: 500 }}>
              <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />or<span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '1.25rem' }}>
              {['email', 'phone'].map((t) => (
                <button key={t} onClick={() => { setTab(t); clearMsg(); }} style={{ flex: 1, textAlign: 'center', padding: '0.5rem', fontSize: '0.82rem', fontWeight: tab === t ? 700 : 500, cursor: 'pointer', background: 'none', border: 'none', borderBottom: tab === t ? '2.5px solid var(--blue)' : '2px solid transparent', marginBottom: -2, color: tab === t ? 'var(--blue)' : '#94a3b8', transition: 'color 0.15s' }}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>

            {/* Email Panel */}
            {tab === 'email' && (
              <>
                {emailView === 'signin' && (
                  <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
                    <div style={fieldWrap}><label htmlFor="signin-email" style={labelStyle}>Email address</label><input id="signin-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} placeholder="you@example.com" /></div>
                    <div style={fieldWrap}><label htmlFor="signin-password" style={labelStyle}>Password</label>
                      <div style={{ position: 'relative' }}>
                        <input id="signin-password" type={showPw ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} style={{ ...inputStyle, paddingRight: '2.5rem' }} placeholder="Your password" onKeyDown={(e) => e.key === 'Enter' && loginWithEmail()} />
                        <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: '0.7rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex' }}>{showPw ? <EyeOff size={15} strokeWidth={2} /> : <Eye size={15} strokeWidth={2} />}</button>
                      </div>
                    </div>
                    <button onClick={loginWithEmail} disabled={loading} style={primaryBtn}>
                      {loading ? <span className="spinner" /> : 'Sign In →'}
                    </button>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.875rem' }}>
                      <button onClick={() => { clearMsg(); setEmailView('register'); }} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Create account</button>
                      <button onClick={forgotPassword} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.8rem' }}>Forgot password?</button>
                    </div>
                  </motion.div>
                )}

                {emailView === 'register' && (
                  <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
                    <div style={fieldWrap}><label htmlFor="reg-name" style={labelStyle}>Full Name</label><input id="reg-name" value={regName} onChange={(e) => setRegName(e.target.value)} style={inputStyle} placeholder="Your full name" /></div>
                    <div style={fieldWrap}><label htmlFor="reg-email" style={labelStyle}>Email address</label><input id="reg-email" type="email" value={regEmail} onChange={(e) => setRegEmail(e.target.value)} style={inputStyle} placeholder="you@example.com" /></div>
                    <div style={fieldWrap}><label htmlFor="reg-phone" style={labelStyle}>Phone <span style={{ color: '#94a3b8', fontWeight: 400 }}>(optional)</span></label><input id="reg-phone" type="tel" value={regPhone} onChange={(e) => setRegPhone(e.target.value)} style={inputStyle} placeholder="+91 98765 43210" /></div>
                    <div style={fieldWrap}><label htmlFor="reg-password" style={labelStyle}>Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 8 · 1 upper · 1 special)</span></label>
                      <div style={{ position: 'relative' }}>
                        <input id="reg-password" type={showRegPw ? 'text' : 'password'} value={regPassword} onChange={(e) => setRegPassword(e.target.value)} style={{ ...inputStyle, paddingRight: '2.5rem' }} placeholder="Choose a password" />
                        <button type="button" onClick={() => setShowRegPw(!showRegPw)} style={{ position: 'absolute', right: '0.7rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8', display: 'flex' }}>{showRegPw ? <EyeOff size={15} strokeWidth={2} /> : <Eye size={15} strokeWidth={2} />}</button>
                      </div>
                    </div>
                    <button onClick={registerWithEmail} disabled={loading} style={primaryBtn}>
                      {loading ? <span className="spinner" /> : 'Create Account →'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.875rem' }}>
                      <button onClick={() => { clearMsg(); setEmailView('signin'); }} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Back to sign in</button>
                    </div>
                  </motion.div>
                )}

                {emailView === 'otp' && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
                    <div style={{ background: 'linear-gradient(135deg, #eff6ff, #dbeafe)', border: '1px solid #bfdbfe', borderRadius: 'var(--radius)', padding: '0.85rem 1rem', marginBottom: '1.25rem', textAlign: 'center' }}>
                      <p style={{ fontSize: '0.84rem', color: '#1e40af', fontWeight: 600, marginBottom: '0.2rem' }}>Check your inbox</p>
                      <p style={{ fontSize: '0.8rem', color: '#3b82f6' }}>6-digit code sent to <strong>{regState.current.email}</strong></p>
                      <p style={{ fontSize: '0.75rem', color: '#60a5fa', marginTop: '0.2rem' }}>Expires in 5 minutes</p>
                    </div>
                    <div style={fieldWrap}><label htmlFor="otp-code" style={labelStyle}>Verification Code</label><input id="otp-code" value={otpCode} onChange={(e) => setOtpCode(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.35rem', letterSpacing: '0.35em', fontWeight: 700 }} maxLength={6} placeholder="••••••" /></div>
                    <button onClick={verifyEmailOTP} disabled={loading} style={primaryBtn}>
                      {loading ? <span className="spinner" /> : 'Verify & Continue'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.875rem' }}>
                      <button onClick={resendEmailOTP} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Resend code</button>
                    </div>
                  </motion.div>
                )}

                {emailView === 'addpwd' && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
                    <div style={{ textAlign: 'center', marginBottom: '1.25rem' }}>
                      <p style={{ fontSize: '0.92rem', color: '#1e3a5f', fontWeight: 700 }}>You signed up with Google</p>
                      <p style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.3rem' }}>Add a password to also sign in with email/password.</p>
                    </div>
                    <div style={fieldWrap}><label htmlFor="add-pwd" style={labelStyle}>New Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 6 chars)</span></label><input id="add-pwd" type="password" value={addPwd} onChange={(e) => setAddPwd(e.target.value)} style={inputStyle} placeholder="Choose a password" /></div>
                    <button onClick={requestAddPassword} disabled={loading} style={primaryBtn}>
                      {loading ? <span className="spinner" /> : 'Add Password'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.875rem' }}><button onClick={() => { clearMsg(); setEmailView('signin'); }} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Back to sign in</button></div>
                  </motion.div>
                )}

                {emailView === 'addpwd-otp' && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
                    <div style={{ background: 'linear-gradient(135deg, #eff6ff, #dbeafe)', border: '1px solid #bfdbfe', borderRadius: 'var(--radius)', padding: '0.85rem 1rem', marginBottom: '1.25rem', textAlign: 'center' }}>
                      <p style={{ fontSize: '0.82rem', color: '#1e40af', fontWeight: 600 }}>Code sent to <strong>{addPwdState.current.email}</strong></p>
                    </div>
                    <div style={fieldWrap}><label htmlFor="addpwd-otp" style={labelStyle}>Verification Code</label><input id="addpwd-otp" value={addPwdOtp} onChange={(e) => setAddPwdOtp(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.35rem', letterSpacing: '0.35em', fontWeight: 700 }} maxLength={6} placeholder="••••••" /></div>
                    <button onClick={verifyAndAddPassword} disabled={loading} style={primaryBtn}>
                      {loading ? <span className="spinner" /> : 'Verify & Add Password'}
                    </button>
                  </motion.div>
                )}
              </>
            )}

            {/* Phone Panel */}
            {tab === 'phone' && (
              <div>
                {phoneStep === 'input' && (
                  <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.2 }}>
                    <div style={fieldWrap}><label htmlFor="phone-number" style={labelStyle}>Phone Number</label><input id="phone-number" type="tel" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} style={inputStyle} placeholder="+91 98765 43210" /></div>
                    <button onClick={sendPhoneOTP} disabled={loading} style={greenBtn}>
                      {loading ? <span className="spinner" /> : 'Send OTP'}
                    </button>
                  </motion.div>
                )}
                {phoneStep === 'otp' && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.22 }}>
                    <div style={{ background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)', border: '1px solid #bbf7d0', borderRadius: 'var(--radius)', padding: '0.85rem 1rem', marginBottom: '1.25rem', textAlign: 'center' }}>
                      <p style={{ fontSize: '0.82rem', color: '#15803d', fontWeight: 600 }}>Code sent to <strong>{phoneNumber}</strong></p>
                    </div>
                    <div style={fieldWrap}><input value={phoneOtp} onChange={(e) => setPhoneOtp(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.35rem', letterSpacing: '0.35em', fontWeight: 700 }} maxLength={6} placeholder="••••••" /></div>
                    <button onClick={verifyPhoneOTP} disabled={loading} style={greenBtn}>
                      {loading ? <span className="spinner" /> : 'Verify Code'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.875rem' }}>
                      <button onClick={() => { setPhoneStep('input'); clearMsg(); }} style={{ background: 'none', border: 'none', color: 'var(--blue)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Change number</button>
                    </div>
                  </motion.div>
                )}
                <div ref={recaptchaRef} id="recaptcha-container" />
              </div>
            )}

            <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.72rem', color: '#94a3b8', paddingTop: '1rem', borderTop: '1px solid #f1f5f9' }}>Vacancy Hai © 2025 — Government Jobs &amp; Exam Tracker</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
