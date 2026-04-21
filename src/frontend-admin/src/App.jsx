import PropTypes from 'prop-types';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import JobForm from './pages/JobForm';
import Admissions from './pages/Admissions';
import AdmissionForm from './pages/AdmissionForm';
import Users from './pages/Users';
import UserDetail from './pages/UserDetail';
import Organizations from './pages/Organizations';
import OrgForm from './pages/OrgForm';
import AuditLogs from './pages/AuditLogs';
import NotFound from './pages/NotFound';

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

ProtectedRoute.propTypes = { children: PropTypes.node.isRequired };

function Guard({ children }) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}

Guard.propTypes = { children: PropTypes.node.isRequired };

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Guard><Layout /></Guard>}>
            <Route index element={<Dashboard />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="jobs/new" element={<JobForm />} />
            <Route path="jobs/:jobId/edit" element={<JobForm />} />
            <Route path="admissions" element={<Admissions />} />
            <Route path="admissions/new" element={<AdmissionForm />} />
            <Route path="admissions/:admissionId/edit" element={<AdmissionForm />} />
            <Route path="users" element={<Users />} />
            <Route path="users/:userId" element={<UserDetail />} />
            <Route path="organizations" element={<Organizations />} />
            <Route path="organizations/new" element={<OrgForm />} />
            <Route path="organizations/:orgId/edit" element={<OrgForm />} />
            <Route path="logs" element={<AuditLogs />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
