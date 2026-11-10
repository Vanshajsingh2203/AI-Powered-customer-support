
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getAgents,
  createAgent,
  updateAgentStatus,
} from '../api/admin';

function AgentManagementPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [updatingAgentId, setUpdatingAgentId] = useState(null);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
  });

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError('');

      const data = await getAgents();

      setAgents(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load agents.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleInputChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleCreateAgent = async (event) => {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError('');
      setSuccess('');

      await createAgent(formData);

      setFormData({
        full_name: '',
        email: '',
        password: '',
      });

      setSuccess('Agent created successfully.');

      await loadAgents();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to create agent.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleStatus = async (agent) => {
    const action = agent.is_active ? 'deactivate' : 'activate';

    const confirmed = window.confirm(
      `Are you sure you want to ${action} ${agent.full_name}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      setUpdatingAgentId(agent.id);
      setError('');
      setSuccess('');

      await updateAgentStatus(
        agent.id,
        !agent.is_active
      );

      setSuccess(
        `Agent ${action}d successfully.`
      );

      await loadAgents();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to update agent status.'
      );
    } finally {
      setUpdatingAgentId(null);
    }
  };

  return (
    <div className="container py-4">

      {/* Page header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <Link
            to="/admin/dashboard"
            className="text-decoration-none"
          >
            &larr; Back to Dashboard
          </Link>

          <h2 className="fw-bold mt-2 mb-1">
            Agent Management
          </h2>

          <p className="text-muted mb-0">
            Create and manage support agents.
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {/* Create agent form */}
      <div className="card border-0 shadow-sm mb-4">
        <div className="card-header bg-white py-3">
          <h5 className="fw-bold mb-0">
            Create New Agent
          </h5>
        </div>

        <div className="card-body">
          <form onSubmit={handleCreateAgent}>
            <div className="row g-3">

              <div className="col-md-4">
                <label className="form-label">
                  Full Name
                </label>

                <input
                  type="text"
                  name="full_name"
                  className="form-control"
                  placeholder="Enter agent name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  minLength={2}
                  maxLength={40}
                  required
                />
              </div>

              <div className="col-md-4">
                <label className="form-label">
                  Email Address
                </label>

                <input
                  type="email"
                  name="email"
                  className="form-control"
                  placeholder="agent@example.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="col-md-4">
                <label className="form-label">
                  Password
                </label>

                <input
                  type="password"
                  name="password"
                  className="form-control"
                  placeholder="Minimum 6 characters"
                  value={formData.password}
                  onChange={handleInputChange}
                  minLength={6}
                  maxLength={128}
                  required
                />
              </div>

              <div className="col-12">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Creating...' : 'Create Agent'}
                </button>
              </div>

            </div>
          </form>
        </div>
      </div>

      {/* Agent list */}
      <div className="card border-0 shadow-sm">
        <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
          <h5 className="fw-bold mb-0">
            All Agents
          </h5>

          <button
            className="btn btn-outline-primary btn-sm"
            onClick={loadAgents}
            disabled={loading}
          >
            Refresh
          </button>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" />
              <p className="text-muted mt-2">
                Loading agents...
              </p>
            </div>
          ) : agents.length === 0 ? (
            <div className="text-center text-muted py-5">
              No agents found.
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead className="table-light">
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {agents.map((agent) => (
                    <tr key={agent.id}>
                      <td className="fw-semibold">
                        {agent.full_name}
                      </td>

                      <td>{agent.email}</td>

                      <td>{agent.role}</td>

                      <td>
                        <span
                          className={`badge ${
                            agent.is_active
                              ? 'bg-success'
                              : 'bg-secondary'
                          }`}
                        >
                          {agent.is_active
                            ? 'Active'
                            : 'Inactive'}
                        </span>
                      </td>

                      <td>
                        {new Date(
                          agent.created_at
                        ).toLocaleDateString()}
                      </td>

                      <td>
                        <button
                          className={`btn btn-sm ${
                            agent.is_active
                              ? 'btn-outline-danger'
                              : 'btn-outline-success'
                          }`}
                          onClick={() =>
                            handleToggleStatus(agent)
                          }
                          disabled={
                            updatingAgentId === agent.id
                          }
                        >
                          {updatingAgentId === agent.id
                            ? 'Updating...'
                            : agent.is_active
                              ? 'Deactivate'
                              : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

export default AgentManagementPage;
