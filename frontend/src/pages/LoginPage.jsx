
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError('');
    setSubmitting(true);

    try {
      const loggedInUser = await login({
        email,
        password,
      });

      // Redirect according to the user's role.
      const dashboardRoutes = {
        CUSTOMER: '/customer/dashboard',
        AGENT: '/agent/dashboard',
        ADMIN: '/admin/dashboard',
      };

      const destination =
        dashboardRoutes[loggedInUser.role] || '/';

      // Return to the originally requested page when possible.
      const requestedPath = location.state?.from?.pathname;

      navigate(requestedPath || destination, {
        replace: true,
      });
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        'Login failed. Please check your credentials and try again.';

      setError(
        typeof message === 'string'
          ? message
          : 'Login failed. Please check your credentials.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container min-vh-100 d-flex align-items-center justify-content-center py-5">
      <div className="card shadow-sm border-0 w-100" style={{ maxWidth: '450px' }}>
        <div className="card-body p-4 p-md-5">
          <div className="text-center mb-4">
            <Link
              to="/"
              className="text-decoration-none text-primary fw-bold fs-3"
            >
              SupportDesk
            </Link>

            <h2 className="fw-bold mt-4">Welcome back</h2>
            <p className="text-muted">
              Sign in to your account to continue.
            </p>
          </div>

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="email" className="form-label">
                Email address
              </label>

              <input
                id="email"
                type="email"
                className="form-control"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="mb-4">
              <label htmlFor="password" className="form-label">
                Password
              </label>

              <input
                id="password"
                type="password"
                className="form-control"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-100 py-2"
              disabled={submitting}
            >
              {submitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="text-center text-muted mt-4 mb-0">
            Don't have an account?{' '}
            <Link to="/register" className="text-decoration-none">
              Create an account
            </Link>
          </p>

          <div className="text-center mt-3">
            <Link to="/" className="text-decoration-none text-muted small">
              Back to home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
