import PropTypes from 'prop-types';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Jobs from './pages/Jobs';
import JobDetail from './pages/JobDetail';
import Admissions from './pages/Admissions';
import AdmissionDetail from './pages/AdmissionDetail';
import AdmitCards from './pages/AdmitCards';
import AdmitCardDetail from './pages/AdmitCardDetail';
import AnswerKeys from './pages/AnswerKeys';
import AnswerKeyDetail from './pages/AnswerKeyDetail';
import Results from './pages/Results';
import ResultDetail from './pages/ResultDetail';
import Profile from './pages/Profile';
import Notifications from './pages/Notifications';
import NotFound from './pages/NotFound';

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

ProtectedRoute.propTypes = { children: PropTypes.node.isRequired };

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="login" element={<Login />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/:slug" element={<JobDetail />} />
            <Route path="admissions" element={<Admissions />} />
            <Route path="admissions/:slug" element={<AdmissionDetail />} />
            <Route path="admit-cards" element={<AdmitCards />} />
            <Route path="admit-cards/:slug" element={<AdmitCardDetail />} />
            <Route path="answer-keys" element={<AnswerKeys />} />
            <Route path="answer-keys/:slug" element={<AnswerKeyDetail />} />
            <Route path="results" element={<Results />} />
            <Route path="results/:slug" element={<ResultDetail />} />
            <Route
              path="profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="notifications"
              element={
                <ProtectedRoute>
                  <Notifications />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
