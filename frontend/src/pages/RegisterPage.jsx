
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);

    try {
      await register({
        full_name: fullName,
        email,
        password,
      });

      setSuccess('Account created successfully! Redirecting to login...');

      setTimeout(() => {
        navigate('/login', { replace: true });
      }, 1500);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        'Registration failed. Please try again.';

      setError(
        typeof message === 'string'
          ? message
          : 'Registration failed. Please check your information.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container min-vh-100 d-flex align-items-center justify-content-center py-5">
      <div className="card shadow-sm border-0 w-100" style={{ maxWidth: '480px' }}>
        <div className="card-body p-4 p-md-5">

          <div className="text-center mb-4">
            <Link
              to="/"
              className="text-decoration-none text-primary fw-bold fs-3"
            >
              SupportDesk
            </Link>

            <h2 className="fw-bold mt-4">Create an account</h2>

            <p className="text-muted">
              Get started with SupportDesk today.
            </p>
          </div>

          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="alert alert-success" role="alert">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="fullName" className="form-label">
                Full name
              </label>

              <input
                id="fullName"
                type="text"
                className="form-control"
                placeholder="Enter your full name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                required
                autoComplete="name"
              />
            </div>

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

            <div className="mb-3">
              <label htmlFor="password" className="form-label">
                Password
              </label>

              <input
                id="password"
                type="password"
                className="form-control"
                placeholder="Create a password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                autoComplete="new-password"
              />
            </div>

            <div className="mb-4">
              <label htmlFor="confirmPassword" className="form-label">
                Confirm password
              </label>

              <input
                id="confirmPassword"
                type="password"
                className="form-control"
                placeholder="Enter your password again"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-100 py-2"
              disabled={submitting}
            >
              {submitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-muted mt-4 mb-0">
            Already have an account?{' '}
            <Link to="/login" className="text-decoration-none">
              Sign in
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

export default RegisterPage;
