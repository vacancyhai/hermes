import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
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
    } catch (_) {}
    login(access_token, refresh_token, name);
    navigate(nextUrl, { replace: true });
  }

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
        } catch (_) { setError('Invalid email or password.'); }
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
    if (!otpCode || otpCode.length !== 6) { setError('Please enter the 6-digit code.'); return; }
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
    } catch (_) { setError('Failed to resend code.'); }
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
    } catch (_) { setError('Failed to send verification code.'); }
    finally { setLoading(false); }
  }

  async function verifyAndAddPassword() {
    if (!addPwdOtp || addPwdOtp.length !== 6) { setError('Please enter the 6-digit code.'); return; }
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

  const inputStyle = { width: '100%', padding: '0.5rem 0.75rem', border: '1.5px solid #e2e8f0', borderRadius: '0.4rem', fontSize: '0.875rem', color: '#1e293b', background: '#f8fafc', outline: 'none' };
  const labelStyle = { display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#374151', marginBottom: '0.25rem' };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '1rem 0', minHeight: '80vh' }}>
      <div style={{ display: 'flex', width: '100%', maxWidth: 860, borderRadius: '0.85rem', overflow: 'hidden', boxShadow: '0 24px 80px rgba(0,0,0,.4)' }}>

        {/* Left branding */}
        <div style={{ flex: '0 0 300px', background: 'linear-gradient(160deg,#0f172a 0%,#1e3a5f 60%,#2563eb 100%)', padding: '2.5rem 2rem', display: 'flex', flexDirection: 'column', justifyContent: 'center', color: '#fff' }} className="hidden sm:flex">
          <div style={{ width: 52, height: 52, background: 'rgba(255,255,255,.15)', borderRadius: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.25rem', fontSize: '1.5rem' }}>🏛</div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.4rem' }}>Vacancy Hai</h1>
          <p style={{ fontSize: '0.85rem', opacity: 0.8, lineHeight: 1.6, marginBottom: '1.75rem' }}>Your one-stop platform for government jobs &amp; admission notifications.</p>
          {['Latest central &amp; state govt jobs', 'NEET, JEE, GATE, CAT &amp; more', 'Admit cards, answer keys &amp; results', 'Personalised job &amp; admission alerts'].map((f) => (
            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.82rem', marginBottom: '0.75rem', opacity: 0.9 }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#60a5fa', flexShrink: 0 }} />
              <span dangerouslySetInnerHTML={{ __html: f }} />
            </div>
          ))}
        </div>

        {/* Right form */}
        <div style={{ flex: 1, background: '#fff', padding: '2rem', overflowY: 'auto', maxHeight: '100vh' }}>
          <div style={{ maxWidth: 340, margin: '0 auto' }}>

            {!FIREBASE_API_KEY && <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.5rem 0.75rem', borderRadius: '0.35rem', marginBottom: '1rem', fontSize: '0.8rem' }}>Firebase not configured. Contact administrator.</div>}
            {error && <div style={{ background: '#fee2e2', color: '#991b1b', padding: '0.4rem 0.7rem', borderRadius: '0.35rem', fontSize: '0.8rem', marginBottom: '0.75rem', border: '1px solid #fecaca' }}>{error}</div>}
            {success && <div style={{ background: '#d1fae5', color: '#065f46', padding: '0.4rem 0.7rem', borderRadius: '0.35rem', fontSize: '0.8rem', marginBottom: '0.75rem', border: '1px solid #a7f3d0' }}>{success}</div>}

            {/* Google */}
            <button onClick={loginWithGoogle} disabled={loading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', width: '100%', padding: '0.5rem', border: '1.5px solid #e2e8f0', borderRadius: '0.4rem', background: '#fff', fontSize: '0.82rem', cursor: 'pointer', fontWeight: 500, color: '#334155' }}>
              <svg viewBox="0 0 24 24" width={16} height={16}><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
              Sign in with Google
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', margin: '0.9rem 0', color: '#94a3b8', fontSize: '0.78rem' }}>
              <span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />or<span style={{ flex: 1, height: 1, background: '#e2e8f0' }} />
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '2px solid #e2e8f0', marginBottom: '1rem' }}>
              {['email', 'phone'].map((t) => (
                <button key={t} onClick={() => { setTab(t); clearMsg(); }} style={{ flex: 1, textAlign: 'center', padding: '0.4rem', fontSize: '0.82rem', fontWeight: 500, cursor: 'pointer', background: 'none', border: 'none', borderBottom: tab === t ? '2px solid #2563eb' : '2px solid transparent', marginBottom: -2, color: tab === t ? '#2563eb' : '#94a3b8' }}>
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>

            {/* Email Panel */}
            {tab === 'email' && (
              <>
                {emailView === 'signin' && (
                  <div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Email address</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inputStyle} placeholder="you@example.com" /></div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Password</label>
                      <div style={{ position: 'relative' }}>
                        <input type={showPw ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} style={{ ...inputStyle, paddingRight: '2.5rem' }} placeholder="Your password" onKeyDown={(e) => e.key === 'Enter' && loginWithEmail()} />
                        <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: '0.6rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>{showPw ? '🙈' : '👁'}</button>
                      </div>
                    </div>
                    <button onClick={loginWithEmail} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer' }}>
                      {loading ? <span className="spinner" /> : 'Sign In →'}
                    </button>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.85rem' }}>
                      <button onClick={() => { clearMsg(); setEmailView('register'); }} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Create account</button>
                      <button onClick={forgotPassword} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Forgot password?</button>
                    </div>
                  </div>
                )}

                {emailView === 'register' && (
                  <div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Full Name</label><input value={regName} onChange={(e) => setRegName(e.target.value)} style={inputStyle} placeholder="Your full name" /></div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Email address</label><input type="email" value={regEmail} onChange={(e) => setRegEmail(e.target.value)} style={inputStyle} placeholder="you@example.com" /></div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Phone <span style={{ color: '#94a3b8', fontWeight: 400 }}>(optional)</span></label><input type="tel" value={regPhone} onChange={(e) => setRegPhone(e.target.value)} style={inputStyle} placeholder="+91 98765 43210" /></div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 8 chars, 1 uppercase, 1 special)</span></label>
                      <div style={{ position: 'relative' }}>
                        <input type={showRegPw ? 'text' : 'password'} value={regPassword} onChange={(e) => setRegPassword(e.target.value)} style={{ ...inputStyle, paddingRight: '2.5rem' }} placeholder="Choose a password" />
                        <button type="button" onClick={() => setShowRegPw(!showRegPw)} style={{ position: 'absolute', right: '0.6rem', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}>{showRegPw ? '🙈' : '👁'}</button>
                      </div>
                    </div>
                    <button onClick={registerWithEmail} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: 'linear-gradient(135deg,#1e3a5f,#2563eb)', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer' }}>
                      {loading ? <span className="spinner" /> : 'Create Account →'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                      <button onClick={() => { clearMsg(); setEmailView('signin'); }} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Back to sign in</button>
                    </div>
                  </div>
                )}

                {emailView === 'otp' && (
                  <div>
                    <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem', textAlign: 'center' }}>
                      We sent a 6-digit code to <strong>{regState.current.email}</strong><br />
                      <span style={{ fontSize: '0.8rem' }}>Check your inbox — expires in 5 minutes.</span>
                    </p>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Verification Code</label><input value={otpCode} onChange={(e) => setOtpCode(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.1rem', letterSpacing: '0.25em' }} maxLength={6} placeholder="000000" /></div>
                    <button onClick={verifyEmailOTP} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: '#2563eb', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}>
                      {loading ? <span className="spinner" /> : 'Verify & Continue'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                      <button onClick={resendEmailOTP} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Resend code</button>
                    </div>
                  </div>
                )}

                {emailView === 'addpwd' && (
                  <div>
                    <p style={{ fontSize: '0.9rem', color: '#1e3a5f', marginBottom: '1rem', textAlign: 'center', fontWeight: 500 }}>You signed up with Google</p>
                    <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem', textAlign: 'center' }}>Add a password to also sign in with email/password.</p>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>New Password <span style={{ color: '#94a3b8', fontWeight: 400 }}>(min 6 chars)</span></label><input type="password" value={addPwd} onChange={(e) => setAddPwd(e.target.value)} style={inputStyle} placeholder="Choose a password" /></div>
                    <button onClick={requestAddPassword} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: '#2563eb', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}>
                      {loading ? <span className="spinner" /> : 'Add Password'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.75rem' }}><button onClick={() => { clearMsg(); setEmailView('signin'); }} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Back to sign in</button></div>
                  </div>
                )}

                {emailView === 'addpwd-otp' && (
                  <div>
                    <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem', textAlign: 'center' }}>
                      We sent a 6-digit code to <strong>{addPwdState.current.email}</strong>
                    </p>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Verification Code</label><input value={addPwdOtp} onChange={(e) => setAddPwdOtp(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.1rem', letterSpacing: '0.25em' }} maxLength={6} placeholder="000000" /></div>
                    <button onClick={verifyAndAddPassword} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: '#2563eb', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}>
                      {loading ? <span className="spinner" /> : 'Verify & Add Password'}
                    </button>
                  </div>
                )}
              </>
            )}

            {/* Phone Panel */}
            {tab === 'phone' && (
              <div>
                {phoneStep === 'input' && (
                  <div>
                    <div style={{ marginBottom: '0.7rem' }}><label style={labelStyle}>Phone Number</label><input type="tel" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} style={inputStyle} placeholder="+91 98765 43210" /></div>
                    <button onClick={sendPhoneOTP} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: '#059669', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer', marginTop: '0.5rem' }}>
                      {loading ? <span className="spinner" /> : 'Send OTP'}
                    </button>
                  </div>
                )}
                {phoneStep === 'otp' && (
                  <div>
                    <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem', textAlign: 'center' }}>Enter the 6-digit code sent to <strong>{phoneNumber}</strong></p>
                    <div style={{ marginBottom: '0.7rem' }}><input value={phoneOtp} onChange={(e) => setPhoneOtp(e.target.value)} style={{ ...inputStyle, textAlign: 'center', fontSize: '1.1rem', letterSpacing: '0.25em' }} maxLength={6} placeholder="000000" /></div>
                    <button onClick={verifyPhoneOTP} disabled={loading} style={{ width: '100%', padding: '0.55rem', borderRadius: '0.4rem', background: '#059669', color: '#fff', fontSize: '0.875rem', fontWeight: 600, border: 'none', cursor: 'pointer' }}>
                      {loading ? <span className="spinner" /> : 'Verify Code'}
                    </button>
                    <div style={{ textAlign: 'center', marginTop: '0.75rem' }}>
                      <button onClick={() => { setPhoneStep('input'); clearMsg(); }} style={{ background: 'none', border: 'none', color: '#2563eb', cursor: 'pointer', fontSize: '0.82rem' }}>Change number</button>
                    </div>
                  </div>
                )}
                <div ref={recaptchaRef} id="recaptcha-container" />
              </div>
            )}

            <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.75rem', color: '#94a3b8' }}>Vacancy Hai © 2025 — Government Jobs & Exam Tracker</div>
          </div>
        </div>
      </div>
    </div>
  );
}
