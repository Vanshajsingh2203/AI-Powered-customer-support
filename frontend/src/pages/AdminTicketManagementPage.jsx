
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getAllTickets,
  getAgents,
  assignTicketToAgent,
} from '../api/admin';

function AdminTicketManagementPage() {
  const [tickets, setTickets] = useState([]);
  const [agents, setAgents] = useState([]);

  const [selectedAgents, setSelectedAgents] = useState({});

  const [loading, setLoading] = useState(true);
  const [assigningTicketId, setAssigningTicketId] = useState(null);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch tickets and active agents.
  const loadData = async () => {
    try {
      setLoading(true);
      setError('');

      const [ticketData, agentData] = await Promise.all([
        getAllTickets({ page: 1, limit: 100 }),
        getAgents(),
      ]);

      setTickets(ticketData.items);
      setAgents(agentData.filter((agent) => agent.is_active));
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load tickets and agents.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Handle agent selection.
  const handleAgentChange = (ticketId, agentId) => {
    setSelectedAgents((previous) => ({
      ...previous,
      [ticketId]: agentId,
    }));
  };

  // Assign or reassign a ticket.
  const handleAssign = async (ticket) => {
    const agentId = selectedAgents[ticket.id];

    if (!agentId) {
      setError('Please select an agent first.');
      return;
    }

    try {
      setAssigningTicketId(ticket.id);
      setError('');
      setSuccess('');

      const assignment = await assignTicketToAgent(
        ticket.id,
        agentId
      );

      const agent = agents.find(
        (item) => item.id === assignment.agent_id
      );

      // Update the ticket with the latest assignment.
      setTickets((previous) =>
        previous.map((item) =>
          item.id === ticket.id
            ? {
                ...item,
                assigned_agent_id: assignment.agent_id,
                assigned_agent_name: agent?.full_name || null,
              }
            : item
        )
      );

      // Clear the agent selection after successful assignment.
      setSelectedAgents((previous) => ({
        ...previous,
        [ticket.id]: '',
      }));

      setSuccess(
        `Ticket "${ticket.title}" assigned to ${
          agent?.full_name || 'the selected agent'
        } successfully.`
      );

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to assign ticket.'
      );
    } finally {
      setAssigningTicketId(null);
    }
  };

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>

        <p className="mt-2">Loading tickets...</p>
      </div>
    );
  }

  return (
    <div className="container-fluid py-4">

      {/* Page heading */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>Ticket Management</h2>
          <p className="text-muted mb-0">
            Assign and reassign tickets to support agents.
          </p>
        </div>

        <Link
          to="/admin/dashboard"
          className="btn btn-outline-secondary"
        >
          Back to Dashboard
        </Link>
      </div>

      {/* Error message */}
      {error && (
        <div className="alert alert-danger">
          {error}
        </div>
      )}

      {/* Success message */}
      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      <div className="card shadow-sm">
        <div className="card-body">

          <div className="d-flex justify-content-between mb-3">
            <h5>All Tickets</h5>

            <span className="badge bg-primary">
              {tickets.length} Tickets Loaded
            </span>
          </div>

          <div className="table-responsive">
            <table className="table table-hover align-middle">

              <thead className="table-light">
                <tr>
                  <th>Ticket</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Assigned Agent</th>
                  <th>Assign / Reassign</th>
                </tr>
              </thead>

              <tbody>
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="text-center py-4">
                      No tickets found.
                    </td>
                  </tr>
                ) : (
                  tickets.map((ticket) => (
                    <tr key={ticket.id}>

                      {/* Ticket information */}
                        <td>
                          <Link
                            to={`/admin/tickets/${ticket.id}`}
                            className="fw-semibold text-decoration-none"
                          >
                            {ticket.title}
                          </Link>
                                        
                          <br />
                                        
                          <small className="text-muted">
                            {ticket.id}
                          </small>
                        </td>
                      {/* Category */}
                      <td>
                        {ticket.category_name || 'Uncategorized'}
                      </td>

                      {/* Status */}
                      <td>
                        <span className="badge bg-secondary">
                          {ticket.status}
                        </span>
                      </td>

                      {/* Priority */}
                      <td>
                        <span className="badge bg-info text-dark">
                          {ticket.priority}
                        </span>
                      </td>

                      {/* Currently assigned agent */}
                      <td>
                        {ticket.assigned_agent_name ? (
                          <span className="badge bg-success">
                            {ticket.assigned_agent_name}
                          </span>
                        ) : (
                          <span className="text-muted">
                            Not assigned
                          </span>
                        )}
                      </td>

                      {/* Assign or reassign agent */}
                      <td>
                        <div className="d-flex gap-2">

                          <select
                            className="form-select form-select-sm"
                            value={selectedAgents[ticket.id] || ''}
                            onChange={(e) =>
                              handleAgentChange(
                                ticket.id,
                                e.target.value
                              )
                            }
                          >
                            <option value="">
                              Select agent
                            </option>

                            {agents.map((agent) => (
                              <option
                                key={agent.id}
                                value={agent.id}
                              >
                                {agent.full_name}
                              </option>
                            ))}
                          </select>

                          <button
                            className="btn btn-sm btn-primary"
                            disabled={
                              assigningTicketId === ticket.id ||
                              !selectedAgents[ticket.id]
                            }
                            onClick={() => handleAssign(ticket)}
                          >
                            {assigningTicketId === ticket.id
                              ? 'Saving...'
                              : 'Assign'}
                          </button>

                        </div>
                      </td>

                    </tr>
                  ))
                )}
              </tbody>

            </table>
          </div>
        </div>
      </div>

    </div>
  );
}

export default AdminTicketManagementPage;





