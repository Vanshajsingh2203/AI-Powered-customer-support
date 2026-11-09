
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import {
  getAgentTicketById,
  updateAssignedTicket,
} from '../api/agents';

import {
  getTicketMessages,
  sendTicketMessage,
} from '../api/tickets';

// Status transitions allowed by the backend.
const allowedStatusTransitions = {
  OPEN: ['IN_PROGRESS'],
  IN_PROGRESS: ['WAITING_ON_CUSTOMER', 'RESOLVED'],
  WAITING_ON_CUSTOMER: ['IN_PROGRESS'],
  RESOLVED: ['IN_PROGRESS', 'CLOSED'],
  CLOSED: [],
};

const priorityOptions = [
  'LOW',
  'MEDIUM',
  'HIGH',
  'URGENT',
];

function AgentTicketDetailsPage() {
  const { ticketId } = useParams();
  const { user } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);

  const [newMessage, setNewMessage] = useState('');

  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [updating, setUpdating] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const loadTicketData = async () => {
      try {
        setLoading(true);
        setError('');

        const [ticketData, messageData] = await Promise.all([
          getAgentTicketById(ticketId),
          getTicketMessages(ticketId, {
            limit: 100,
            offset: 0,
          }),
        ]);

        setTicket(ticketData);
        setMessages(messageData);

        setSelectedStatus(ticketData.status);
        setSelectedPriority(ticketData.priority);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          'Unable to load ticket details.'
        );
      } finally {
        setLoading(false);
      }
    };

    loadTicketData();
  }, [ticketId]);

  const handleSendMessage = async (event) => {
    event.preventDefault();

    const content = newMessage.trim();

    if (!content) {
      return;
    }

    try {
      setSending(true);
      setError('');
      setSuccess('');

      const sentMessage = await sendTicketMessage(ticketId, {
        content,
      });

      setMessages((previousMessages) => [
        ...previousMessages,
        sentMessage,
      ]);

      setNewMessage('');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to send message.'
      );
    } finally {
      setSending(false);
    }
  };

  const handleUpdateTicket = async (event) => {
    event.preventDefault();

    const updateData = {};

    if (selectedStatus !== ticket.status) {
      updateData.status = selectedStatus;
    }

    if (selectedPriority !== ticket.priority) {
      updateData.priority = selectedPriority;
    }

    if (Object.keys(updateData).length === 0) {
      setError('Please change the status or priority first.');
      return;
    }

    try {
      setUpdating(true);
      setError('');
      setSuccess('');

      const updatedTicket = await updateAssignedTicket(
        ticketId,
        updateData
      );

      setTicket(updatedTicket);
      setSelectedStatus(updatedTicket.status);
      setSelectedPriority(updatedTicket.priority);

      setSuccess('Ticket updated successfully.');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to update ticket.'
      );
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" />
        <p className="mt-3">Loading ticket...</p>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">
          {error || 'Ticket not found.'}
        </div>

        <Link to="/agent/dashboard" className="btn btn-primary">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const availableStatuses = [
    ticket.status,
    ...(allowedStatusTransitions[ticket.status] || []),
  ];

  return (
    <div className="container py-4">
      <div className="mb-4">
        <Link
          to="/agent/dashboard"
          className="text-decoration-none"
        >
          &larr; Back to Agent Dashboard
        </Link>
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

      {/* Ticket information */}
      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <h3>{ticket.title}</h3>

          <p className="text-muted mb-3">
            Ticket ID: {ticket.id}
          </p>

          <p>{ticket.description}</p>

          <div className="d-flex flex-wrap gap-3">
            <span className="badge bg-primary">
              Status: {ticket.status}
            </span>

            <span className="badge bg-warning text-dark">
              Priority: {ticket.priority}
            </span>

            <span className="badge bg-secondary">
              Category: {ticket.category_name || 'Uncategorized'}
            </span>
          </div>
        </div>
      </div>

      {/* Status and priority management */}
      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white">
          <h5 className="mb-0">Manage Ticket</h5>
        </div>

        <div className="card-body">
          <form onSubmit={handleUpdateTicket}>
            <div className="row g-3">
              <div className="col-md-5">
                <label className="form-label">
                  Ticket Status
                </label>

                <select
                  className="form-select"
                  value={selectedStatus}
                  onChange={(event) =>
                    setSelectedStatus(event.target.value)
                  }
                  disabled={updating}
                >
                  {availableStatuses.map((status) => (
                    <option key={status} value={status}>
                      {status.replaceAll('_', ' ')}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-md-5">
                <label className="form-label">
                  Priority
                </label>

                <select
                  className="form-select"
                  value={selectedPriority}
                  onChange={(event) =>
                    setSelectedPriority(event.target.value)
                  }
                  disabled={updating}
                >
                  {priorityOptions.map((priority) => (
                    <option key={priority} value={priority}>
                      {priority}
                    </option>
                  ))}
                </select>
              </div>

              <div className="col-md-2 d-flex align-items-end">
                <button
                  type="submit"
                  className="btn btn-primary w-100"
                  disabled={updating}
                >
                  {updating ? 'Saving...' : 'Update'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>

      {/* Conversation */}
      <div className="card shadow-sm">
        <div className="card-header bg-white">
          <h5 className="mb-0">Conversation</h5>
        </div>

        <div
          className="card-body"
          style={{
            maxHeight: '450px',
            overflowY: 'auto',
          }}
        >
          {messages.length === 0 ? (
            <p className="text-muted text-center">
              No messages yet.
            </p>
          ) : (
            messages.map((message) => {
              const isOwnMessage =
                message.sender_id === user?.id;

              return (
                <div
                  key={message.id}
                  className={`d-flex mb-3 ${
                    isOwnMessage
                      ? 'justify-content-end'
                      : 'justify-content-start'
                  }`}
                >
                  <div
                    className={`p-3 rounded ${
                      isOwnMessage
                        ? 'bg-primary text-white'
                        : 'bg-light'
                    }`}
                    style={{ maxWidth: '75%' }}
                  >
                    <div className="small mb-1 fw-bold">
                      {isOwnMessage ? 'You' : 'Customer'}
                    </div>

                    <div>{message.content}</div>

                    <div className="small mt-2 opacity-75">
                      {new Date(
                        message.created_at
                      ).toLocaleString()}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="card-footer bg-white">
          <form onSubmit={handleSendMessage}>
            <div className="input-group">
              <input
                type="text"
                className="form-control"
                placeholder="Write a reply to the customer..."
                value={newMessage}
                onChange={(event) =>
                  setNewMessage(event.target.value)
                }
                disabled={sending}
              />

              <button
                type="submit"
                className="btn btn-primary"
                disabled={sending || !newMessage.trim()}
              >
                {sending ? 'Sending...' : 'Send Reply'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default AgentTicketDetailsPage;
