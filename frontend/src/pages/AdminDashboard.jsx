
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { getAllTickets } from '../api/admin';

function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalTickets, setTotalTickets] = useState(0);

  // Fetch tickets from the backend.
  const loadTickets = async (pageNumber = page, filters = {}) => {
    try {
      setLoading(true);
      setError('');

      const params = {
        page: pageNumber,
        limit: 10,
        sort_order: 'desc',
      };

      if (filters.search?.trim()) {
        params.search = filters.search.trim();
      }

      if (filters.status) {
        params.status = filters.status;
      }

      if (filters.priority) {
        params.priority = filters.priority;
      }

      const data = await getAllTickets(params);

      setTickets(data.items);
      setTotalPages(data.total_pages);
      setTotalTickets(data.total);
      setPage(data.page);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load tickets.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets(1);
  }, []);

  // Search tickets.
  const handleSearch = (event) => {
    event.preventDefault();

    loadTickets(1, {
      search,
      status,
      priority,
    });
  };

  // Handle filter changes.
  const handleFilterChange = (setter) => (event) => {
    setter(event.target.value);
  };

  // Reset all filters.
  const handleReset = () => {
    setSearch('');
    setStatus('');
    setPriority('');

    loadTickets(1, {
      search: '',
      status: '',
      priority: '',
    });
  };

  // Logout.
  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  // Navigate to agent management.
  const handleManageAgents = () => {
    navigate('/admin/agents');
  };

  // Status badge styling.
  const getStatusClass = (ticketStatus) => {
    const classes = {
      OPEN: 'bg-primary',
      IN_PROGRESS: 'bg-info text-dark',
      WAITING_ON_CUSTOMER: 'bg-warning text-dark',
      RESOLVED: 'bg-success',
      CLOSED: 'bg-secondary',
    };

    return classes[ticketStatus] || 'bg-secondary';
  };

  // Priority badge styling.
  const getPriorityClass = (ticketPriority) => {
    const classes = {
      LOW: 'bg-secondary',
      MEDIUM: 'bg-info text-dark',
      HIGH: 'bg-warning text-dark',
      URGENT: 'bg-danger',
    };

    return classes[ticketPriority] || 'bg-secondary';
  };

  return (
    <div className="container-fluid py-4 px-4">

      {/* Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4">
        <div>
          <h2 className="fw-bold mb-1">
            Admin Dashboard
          </h2>

          <p className="text-muted mb-0">
            Welcome, {user?.full_name}
          </p>
        </div>

        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-primary"
            onClick={handleManageAgents}
          >
            Manage Agents
          </button>
          <button
            className="btn btn-outline-primary me-2"
            onClick={() => navigate('/admin/customers')}
          >
            Manage Customers
          </button>
          <button
            className="btn btn-outline-primary me-2"
            onClick={() => navigate('/admin/tickets')}
          >
            Manage Tickets
          </button>
          <button
            className="btn btn-outline-primary me-2"
            onClick={() => navigate('/admin/categories')}
          >
            Manage Categories
          </button>
          <button
            className="btn btn-danger"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Ticket summary */}
      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card border-0 shadow-sm">
            <div className="card-body">
              <p className="text-muted mb-1">
                Total Tickets
              </p>

              <h3 className="fw-bold mb-0">
                {totalTickets}
              </h3>
            </div>
          </div>
        </div>
      </div>

      {/* Ticket management */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white py-3">
          <h5 className="fw-bold mb-0">
            All Support Tickets
          </h5>
        </div>

        <div className="card-body">

          {/* Search and filters */}
          <form
            onSubmit={handleSearch}
            className="row g-3 mb-4"
          >
            <div className="col-lg-5">
              <input
                type="text"
                className="form-control"
                placeholder="Search tickets..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />
            </div>

            <div className="col-lg-3">
              <select
                className="form-select"
                value={status}
                onChange={handleFilterChange(setStatus)}
              >
                <option value="">All Statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">
                  In Progress
                </option>
                <option value="WAITING_ON_CUSTOMER">
                  Waiting on Customer
                </option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>

            <div className="col-lg-2">
              <select
                className="form-select"
                value={priority}
                onChange={handleFilterChange(setPriority)}
              >
                <option value="">All Priorities</option>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="URGENT">Urgent</option>
              </select>
            </div>

            <div className="col-lg-2 d-flex gap-2">
              <button
                type="submit"
                className="btn btn-primary flex-grow-1"
              >
                Search
              </button>

              <button
                type="button"
                className="btn btn-outline-secondary"
                onClick={handleReset}
              >
                Reset
              </button>
            </div>
          </form>

          {/* Error message */}
          {error && (
            <div className="alert alert-danger">
              {error}
            </div>
          )}

          {/* Tickets table */}
          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" />

              <p className="mt-2 text-muted">
                Loading tickets...
              </p>
            </div>
          ) : tickets.length === 0 ? (
            <div className="text-center py-5 text-muted">
              No tickets found.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead className="table-light">
                  <tr>
                    <th>Ticket</th>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Created At</th>
                  </tr>
                </thead>

                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.id}>
                      <td>
                        <div className="fw-semibold">
                          {ticket.title}
                        </div>

                        <small className="text-muted">
                          ID: {ticket.id}
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
                        {new Date(
                          ticket.created_at
                        ).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {!loading && tickets.length > 0 && (
            <div className="d-flex justify-content-between align-items-center mt-3">
              <small className="text-muted">
                Page {page} of {totalPages}
              </small>

              <div className="d-flex gap-2">
                <button
                  className="btn btn-outline-primary btn-sm"
                  disabled={page <= 1}
                  onClick={() => loadTickets(page - 1, {
                    search,
                    status,
                    priority,
                  })}
                >
                  Previous
                </button>

                <button
                  className="btn btn-outline-primary btn-sm"
                  disabled={page >= totalPages}
                  onClick={() => loadTickets(page + 1, {
                    search,
                    status,
                    priority,
                  })}
                >
                  Next
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;
