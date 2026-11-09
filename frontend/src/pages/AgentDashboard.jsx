
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { getAssignedTickets } from '../api/agents';

function AgentDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch tickets whenever filters or pagination change.
  useEffect(() => {
    const fetchTickets = async () => {
      setLoading(true);
      setError('');

      try {
        const data = await getAssignedTickets({
          page,
          limit: 10,
          status: status || undefined,
          priority: priority || undefined,
          search: search || undefined,
          sort_order: 'desc',
        });

        setTickets(data.items);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch (err) {
        console.error('Failed to fetch assigned tickets:', err);

        const message = err.response?.data?.detail;

        setError(
          typeof message === 'string'
            ? message
            : 'Unable to load assigned tickets. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [page, status, priority, search]);

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

  // Format dates.
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
  const getPriorityClass = (ticketPriority) => {
    const classes = {
      LOW: 'bg-success-subtle text-success-emphasis',
      MEDIUM: 'bg-info-subtle text-info-emphasis',
      HIGH: 'bg-warning-subtle text-warning-emphasis',
      URGENT: 'bg-danger-subtle text-danger-emphasis',
    };

    return classes[ticketPriority] || 'bg-secondary-subtle text-secondary';
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

            <span className="badge bg-success-subtle text-success p-2">
              Support Agent
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
        <div className="mb-4">
          <h2 className="fw-bold mb-1">
            Agent Dashboard
          </h2>

          <p className="text-muted mb-0">
            Manage your assigned support tickets and assist customers.
          </p>
        </div>

        {/* Total Tickets */}
        <div className="row mb-4">
          <div className="col-md-4 col-lg-3">
            <div className="card border-0 shadow-sm">
              <div className="card-body p-4">
                <p className="text-muted mb-2">
                  Assigned Tickets
                </p>

                <h2 className="fw-bold mb-0">
                  {loading ? '...' : total}
                </h2>
              </div>
            </div>
          </div>
        </div>

        {/* Assigned Tickets */}
        <div className="card border-0 shadow-sm">
          <div className="card-body p-4">

            <div className="mb-4">
              <h4 className="fw-bold mb-1">
                My Assigned Tickets
              </h4>

              <p className="text-muted mb-0 small">
                View and manage tickets assigned to you.
              </p>
            </div>

            {/* Search and Filters */}
            <form
              onSubmit={handleSearch}
              className="row g-3 mb-4"
            >
              <div className="col-md-5">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search tickets..."
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

              <div className="col-md-2">
                <select
                  className="form-select"
                  value={priority}
                  onChange={(event) => {
                    setPriority(event.target.value);
                    setPage(1);
                  }}
                >
                  <option value="">All Priorities</option>
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                </select>
              </div>

              <div className="col-md-2">
                <button
                  type="submit"
                  className="btn btn-primary w-100"
                >
                  Search
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
                  Loading assigned tickets...
                </p>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && tickets.length === 0 && (
              <div className="text-center py-5">
                <h5 className="fw-bold">
                  No assigned tickets
                </h5>

                <p className="text-muted mb-0">
                  There are currently no tickets assigned to you.
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
                              to={`/agent/tickets/${ticket.id}`}
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

export default AgentDashboard;
