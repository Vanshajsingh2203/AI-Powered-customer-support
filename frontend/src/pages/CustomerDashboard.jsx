
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { getCustomerTickets } from '../api/tickets';
import { useAuth } from '../context/AuthContext';



function CustomerDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const [status, setStatus] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch tickets whenever the page or filters change.
  useEffect(() => {
    const fetchTickets = async () => {
      setLoading(true);
      setError('');

      try {
        const data = await getCustomerTickets({
          page,
          limit: 10,
          status: status || undefined,
          search: search || undefined,
          sort_order: 'desc',
        });

        setTickets(data.items);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch (err) {
        console.error('Failed to fetch tickets:', err);

        const message = err.response?.data?.detail;

        setError(
          typeof message === 'string'
            ? message
            : 'Unable to load your tickets. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [page, status, search]);

  // Search tickets.
  const handleSearch = (event) => {
    event.preventDefault();
    setPage(1);
    setSearch(searchInput.trim());
  };

  // Logout.
  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  // Format date.
  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  // Status badge styling.
  const getStatusClass = (ticketStatus) => {
    const classes = {
      OPEN: 'bg-primary-subtle text-primary',
      IN_PROGRESS: 'bg-warning-subtle text-warning-emphasis',
      WAITING_ON_CUSTOMER: 'bg-info-subtle text-info-emphasis',
      RESOLVED: 'bg-success-subtle text-success-emphasis',
      CLOSED: 'bg-secondary-subtle text-secondary-emphasis',
    };

    return classes[ticketStatus] || 'bg-secondary-subtle text-secondary';
  };

  // Priority badge styling.
  const getPriorityClass = (priority) => {
    const classes = {
      LOW: 'bg-success-subtle text-success-emphasis',
      MEDIUM: 'bg-info-subtle text-info-emphasis',
      HIGH: 'bg-warning-subtle text-warning-emphasis',
      URGENT: 'bg-danger-subtle text-danger-emphasis',
    };

    return classes[priority] || 'bg-secondary-subtle text-secondary';
  };

  return (
    <div className="min-vh-100 bg-light">

      {/* Navigation */}
      <nav className="navbar navbar-expand-lg bg-white shadow-sm">
        <div className="container">
          <Link
            to="/"
            className="navbar-brand fw-bold text-primary fs-4"
          >
            SupportDesk
          </Link>

          <div className="d-flex align-items-center gap-3">
            <span className="text-muted d-none d-md-inline">
              {user?.full_name}
            </span>

            <button
              className="btn btn-outline-danger btn-sm"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container py-5">

        {/* Dashboard Heading */}
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
          <div>
            <h2 className="fw-bold mb-1">
              Customer Dashboard
            </h2>

            <p className="text-muted mb-0">
              Welcome back, {user?.full_name}.
              Manage and track your support requests here.
            </p>
          </div>

          <div className="d-flex align-items-center gap-3 flex-wrap">
            <span className="badge bg-primary-subtle text-primary p-2">
              Customer Account
            </span>

            <Link
              to="/customer/tickets/create"
              className="btn btn-primary"
            >
              + Create New Ticket
            </Link>
          </div>
        </div>

        {/* Total Tickets */}
        <div className="row mb-4">
          <div className="col-md-4 col-lg-3">
            <div className="card border-0 shadow-sm">
              <div className="card-body p-4">
                <p className="text-muted mb-2">
                  Total Tickets
                </p>

                <h2 className="fw-bold mb-0">
                  {loading ? '...' : total}
                </h2>
              </div>
            </div>
          </div>
        </div>

        {/* Ticket Section */}
        <div className="card border-0 shadow-sm">

          <div className="card-body p-4">

            <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center mb-4 gap-3">
              <div>
                <h4 className="fw-bold mb-1">
                  My Support Tickets
                </h4>

                <p className="text-muted mb-0 small">
                  View and track your submitted requests.
                </p>
              </div>
            </div>

            {/* Search and Filter */}
            <form
              onSubmit={handleSearch}
              className="row g-3 mb-4"
            >
              <div className="col-md-6">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search by ticket title or description..."
                  value={searchInput}
                  onChange={(event) =>
                    setSearchInput(event.target.value)
                  }
                />
              </div>

              <div className="col-md-3">
                <select
                  className="form-select"
                  value={status}
                  onChange={(event) => {
                    setStatus(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="WAITING_ON_CUSTOMER">
                    Waiting on Customer
                  </option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>

              <div className="col-md-3">
                <button
                  type="submit"
                  className="btn btn-primary w-100"
                >
                  Search Tickets
                </button>
              </div>
            </form>

            {/* Error */}
            {error && (
              <div className="alert alert-danger">
                {error}
              </div>
            )}

            {/* Loading */}
            {loading && (
              <div className="text-center py-5">
                <div
                  className="spinner-border text-primary"
                  role="status"
                >
                  <span className="visually-hidden">
                    Loading...
                  </span>
                </div>

                <p className="text-muted mt-3">
                  Loading your tickets...
                </p>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && tickets.length === 0 && (
              <div className="text-center py-5">
                <h5 className="fw-bold">
                  No tickets found
                </h5>

                <p className="text-muted mb-0">
                  You haven't created any matching support tickets yet.
                </p>
              </div>
            )}

            {/* Ticket Table */}
            {!loading && !error && tickets.length > 0 && (
              <>
                <div className="table-responsive">
                  <table className="table align-middle">
                    <thead className="table-light">
                      <tr>
                        <th>Ticket</th>
                        <th>Category</th>
                        <th>Status</th>
                        <th>Priority</th>
                        <th>Created</th>
                      </tr>
                    </thead>

                    <tbody>
                      {tickets.map((ticket) => (
                        <tr key={ticket.id}>
                          <td>
                            <Link
                              to={`/customer/tickets/${ticket.id}`}
                              className="fw-semibold text-decoration-none"
                            >
                              {ticket.title}
                            </Link>

                            <div
                              className="text-muted small"
                              style={{ maxWidth: '280px' }}
                            >
                              {ticket.description.length > 65
                                ? `${ticket.description.substring(0, 65)}...`
                                : ticket.description}
                            </div>

                            <small className="text-muted">
                              ID: {ticket.id.substring(0, 8)}
                            </small>
                          </td>

                          <td>
                            {ticket.category_name || 'Uncategorized'}
                          </td>

                          <td>
                            <span
                              className={`badge ${getStatusClass(ticket.status)}`}
                            >
                              {ticket.status.replaceAll('_', ' ')}
                            </span>
                          </td>

                          <td>
                            <span
                              className={`badge ${getPriorityClass(ticket.priority)}`}
                            >
                              {ticket.priority}
                            </span>
                          </td>

                          <td>
                            {formatDate(ticket.created_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="d-flex flex-column flex-md-row justify-content-between align-items-center mt-4 gap-3">

                  <p className="text-muted mb-0 small">
                    Showing {tickets.length} of {total} tickets
                    (Page {page} of {totalPages})
                  </p>

                  <div className="d-flex gap-2">
                    <button
                      className="btn btn-outline-primary btn-sm"
                      disabled={page <= 1 || loading}
                      onClick={() => setPage((current) => current - 1)}
                    >
                      Previous
                    </button>

                    <button
                      className="btn btn-outline-primary btn-sm"
                      disabled={page >= totalPages || loading}
                      onClick={() => setPage((current) => current + 1)}
                    >
                      Next
                    </button>
                  </div>

                </div>
              </>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}

export default CustomerDashboard;
