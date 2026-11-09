
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom';
import CustomerDashboard from './pages/CustomerDashboard';
import CreateTicketPage from './pages/CreateTicketPage';
import { useAuth } from './context/AuthContext';
import ProtectedRoute from './routes/ProtectedRoute';

import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Homepage
function HomePage() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const dashboardRoutes = {
    CUSTOMER: '/customer/dashboard',
    AGENT: '/agent/dashboard',
    ADMIN: '/admin/dashboard',
  };

  const handleLogout = async () => {
    await logout();
    navigate('/', { replace: true });
  };

  return (
    <div className="min-vh-100 d-flex flex-column">
      <nav className="navbar navbar-expand-lg bg-white shadow-sm">
        <div className="container">
          <Link className="navbar-brand fw-bold text-primary fs-4" to="/">
            SupportDesk
          </Link>

          <div className="d-flex align-items-center gap-2">
            {isAuthenticated ? (
              <>
                <span className="text-muted small d-none d-md-inline">
                  Hello, {user?.full_name}
                </span>

                <Link
                  to={dashboardRoutes[user?.role] || '/'}
                  className="btn btn-outline-primary"
                >
                  Dashboard
                </Link>

                <button
                  className="btn btn-danger"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-outline-primary">
                  Login
                </Link>

                <Link to="/register" className="btn btn-primary">
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      <main className="container flex-grow-1 d-flex align-items-center justify-content-center py-5">
        <div className="text-center" style={{ maxWidth: '750px' }}>
          <span className="badge bg-primary-subtle text-primary mb-3 p-2">
            AI-Powered Customer Support
          </span>

          <h1 className="display-4 fw-bold mb-4">
            Customer Support, Made Simpler.
          </h1>

          <p className="lead text-muted mb-4">
            Create support tickets, track their progress, and
            communicate with support agents through one platform.
          </p>

          {!isAuthenticated && (
            <div className="d-flex justify-content-center gap-3">
              <Link to="/register" className="btn btn-primary btn-lg">
                Get Started
              </Link>

              <Link to="/login" className="btn btn-outline-secondary btn-lg">
                Sign In
              </Link>
            </div>
          )}

          <div className="row g-4 mt-5 text-start">
            <div className="col-md-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h5 className="fw-bold">Create Tickets</h5>
                  <p className="text-muted mb-0">
                    Submit your problems and get help from support agents.
                  </p>
                </div>
              </div>
            </div>

            <div className="col-md-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h5 className="fw-bold">Track Progress</h5>
                  <p className="text-muted mb-0">
                    Monitor the status of your support requests.
                  </p>
                </div>
              </div>
            </div>

            <div className="col-md-4">
              <div className="card h-100 border-0 shadow-sm">
                <div className="card-body p-4">
                  <h5 className="fw-bold">AI Assistance</h5>
                  <p className="text-muted mb-0">
                    Get smarter support with AI-powered assistance.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="text-center text-muted py-3 border-top bg-white">
        <small>SupportDesk — Customer Support Platform</small>
      </footer>
    </div>
  );
}

// Temporary dashboard placeholder.
// We will replace these with actual dashboards later.
function DashboardPlaceholder({ role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="container py-5">
      <div className="card border-0 shadow-sm">
        <div className="card-body p-5">
          <h2 className="fw-bold">
            {role} Dashboard
          </h2>

          <p className="text-muted">
            Welcome, {user?.full_name}.
          </p>

          <p>
            Authentication and role-based access are working.
            We will build the actual dashboard here.
          </p>

          <button
            className="btn btn-danger"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}

// Access denied page
function UnauthorizedPage() {
  return (
    <div className="container min-vh-100 d-flex flex-column justify-content-center align-items-center">
      <h1 className="display-4 fw-bold text-danger">403</h1>

      <h3>Access Denied</h3>

      <p className="text-muted">
        You do not have permission to access this page.
      </p>

      <Link to="/" className="btn btn-primary">
        Return Home
      </Link>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />

        <Route path="/login" element={<LoginPage />} />

        <Route path="/register" element={<RegisterPage />} />

        <Route
          path="/customer/dashboard"
          element={
            <ProtectedRoute allowedRoles={['CUSTOMER']}>
              <CustomerDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/agent/dashboard"
          element={
            <ProtectedRoute allowedRoles={['AGENT']}>
              <DashboardPlaceholder role="Agent" />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <DashboardPlaceholder role="Admin" />
            </ProtectedRoute>
          }
        />
        <Route
          path="/customer/tickets/create"
          element={
            <ProtectedRoute allowedRoles={['CUSTOMER']}>
              <CreateTicketPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/unauthorized"
          element={<UnauthorizedPage />}
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
