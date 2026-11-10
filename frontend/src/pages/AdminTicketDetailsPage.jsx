
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

import {
  getAdminTicketById,
  updateAdminTicket,
} from '../api/admin';

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

const roleLabels = {
  CUSTOMER: 'Customer',
  AGENT: 'Agent',
  ADMIN: 'Administrator',
};

function AdminTicketDetailsPage() {
  const { ticketId } = useParams();
  const { user } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);

  const [newMessage, setNewMessage] = useState('');

  // PUBLIC or INTERNAL.
  const [activeTab, setActiveTab] = useState('PUBLIC');

  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [updating, setUpdating] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Load ticket and conversation.
  useEffect(() => {
    const loadTicketData = async () => {
      try {
        setLoading(true);
        setError('');

        const [ticketData, messageData] = await Promise.all([
          getAdminTicketById(ticketId),
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

  // Send a public reply or internal note.
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
        is_internal: activeTab === 'INTERNAL',
      });

      setMessages((previousMessages) => [
        ...previousMessages,
        sentMessage,
      ]);

      setNewMessage('');

      setSuccess(
        activeTab === 'INTERNAL'
          ? 'Internal note added successfully.'
          : 'Public reply sent successfully.'
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to send message.'
      );
    } finally {
      setSending(false);
    }
  };

  // Update ticket status or priority.
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

      const updatedTicket = await updateAdminTicket(
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

        <Link to="/admin/tickets" className="btn btn-primary">
          Back to Ticket Management
        </Link>
      </div>
    );
  }

  const availableStatuses = [
    ticket.status,
    ...(allowedStatusTransitions[ticket.status] || []),
  ];

  // Display messages belonging to the selected tab.
  const visibleMessages = messages.filter((message) =>
    activeTab === 'INTERNAL'
      ? message.is_internal
      : !message.is_internal
  );

  const publicMessageCount = messages.filter(
    (message) => !message.is_internal
  ).length;

  const internalMessageCount = messages.filter(
    (message) => message.is_internal
  ).length;

  return (
    <div className="container py-4">

      {/* Navigation */}
      <div className="mb-4">
        <Link
          to="/admin/tickets"
          className="text-decoration-none"
        >
          &larr; Back to Ticket Management
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className="alert alert-danger">
          {error}
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {/* Ticket information */}
      <div className="card shadow-sm mb-4">
        <div className="card-header bg-white">
          <h5 className="mb-0">Ticket Information</h5>
        </div>

        <div className="card-body">
          <h3>{ticket.title}</h3>

          <p className="text-muted">
            Ticket ID: {ticket.id}
          </p>

          <p>{ticket.description}</p>

          <hr />

          <div className="row g-3">

            <div className="col-md-6">
              <strong>Customer</strong>

              <p className="mb-1">
                {ticket.customer_name || 'Not available'}
              </p>

              <small className="text-muted">
                {ticket.customer_email || ''}
              </small>
            </div>

            <div className="col-md-6">
              <strong>Assigned Agent</strong>

              <p className="mb-0">
                {ticket.assigned_agent_name || 'Not assigned'}
              </p>
            </div>

            <div className="col-md-4">
              <strong>Category</strong>

              <p>
                {ticket.category_name || 'Uncategorized'}
              </p>
            </div>

            <div className="col-md-4">
              <strong>Status</strong>

              <p>
                <span className="badge bg-primary">
                  {ticket.status}
                </span>
              </p>
            </div>

            <div className="col-md-4">
              <strong>Priority</strong>

              <p>
                <span className="badge bg-warning text-dark">
                  {ticket.priority}
                </span>
              </p>
            </div>

          </div>
        </div>
      </div>

      {/* Ticket management */}
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
          <h5 className="mb-1">Ticket Conversation</h5>

          <small className="text-muted">
            Communicate with the customer or discuss the ticket privately with staff.
          </small>
        </div>

        {/* Conversation tabs */}
        <div className="card-header bg-white border-top">
          <ul className="nav nav-tabs card-header-tabs">

            <li className="nav-item">
              <button
                type="button"
                className={`nav-link ${
                  activeTab === 'PUBLIC' ? 'active' : ''
                }`}
                onClick={() => {
                  setActiveTab('PUBLIC');
                  setError('');
                  setSuccess('');
                }}
              >
                Public Conversation
                <span className="badge bg-success ms-2">
                  {publicMessageCount}
                </span>
              </button>
            </li>

            <li className="nav-item">
              <button
                type="button"
                className={`nav-link ${
                  activeTab === 'INTERNAL' ? 'active' : ''
                }`}
                onClick={() => {
                  setActiveTab('INTERNAL');
                  setError('');
                  setSuccess('');
                }}
              >
                Internal Discussion
                <span className="badge bg-warning text-dark ms-2">
                  {internalMessageCount}
                </span>
              </button>
            </li>

          </ul>
        </div>

        {/* Messages */}
        <div
          className="card-body"
          style={{
            minHeight: '300px',
            maxHeight: '500px',
            overflowY: 'auto',
          }}
        >

          {visibleMessages.length === 0 ? (
            <div className="text-center text-muted py-5">
              <h6>
                {activeTab === 'INTERNAL'
                  ? 'No internal discussions yet.'
                  : 'No public messages yet.'}
              </h6>

              <p className="mb-0 small">
                {activeTab === 'INTERNAL'
                  ? 'Internal notes added by staff will appear here.'
                  : 'Customer messages and public replies will appear here.'}
              </p>
            </div>
          ) : (
            visibleMessages.map((message) => {
              const isOwnMessage =
                message.sender_id === user?.id;

              const senderRole =
                roleLabels[message.sender_role] ||
                message.sender_role ||
                'Unknown Role';

              const senderName = isOwnMessage
                ? 'You'
                : message.sender_name || senderRole;

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
                      activeTab === 'INTERNAL'
                        ? 'bg-warning-subtle border border-warning'
                        : isOwnMessage
                          ? 'bg-primary text-white'
                          : 'bg-light border'
                    }`}
                    style={{ maxWidth: '80%' }}
                  >

                    {/* Sender information */}
                    <div className="d-flex flex-wrap gap-2 align-items-center mb-2">

                      <strong className="small">
                        {senderName}
                      </strong>

                      <span className="badge bg-secondary">
                        {senderRole}
                      </span>

                    </div>

                    {/* Message content */}
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </div>

                    {/* Timestamp */}
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

        {/* Message composer */}
        <div className="card-footer bg-white">

          <form onSubmit={handleSendMessage}>

            {activeTab === 'PUBLIC' ? (
              <div className="alert alert-success py-2">
                <strong>Public Reply:</strong> This message will be visible to the customer, agents and administrators.
              </div>
            ) : (
              <div className="alert alert-warning py-2">
                <strong>Internal Discussion:</strong> This message will only be visible to agents and administrators.
              </div>
            )}

            <div className="input-group">

              <input
                type="text"
                className="form-control"
                placeholder={
                  activeTab === 'INTERNAL'
                    ? 'Write an internal note for staff...'
                    : 'Write a reply to the customer...'
                }
                value={newMessage}
                onChange={(event) =>
                  setNewMessage(event.target.value)
                }
                disabled={sending}
              />

              <button
                type="submit"
                className={`btn ${
                  activeTab === 'INTERNAL'
                    ? 'btn-warning'
                    : 'btn-primary'
                }`}
                disabled={sending || !newMessage.trim()}
              >
                {sending
                  ? 'Sending...'
                  : activeTab === 'INTERNAL'
                    ? 'Add Internal Note'
                    : 'Send Public Reply'}
              </button>

            </div>

          </form>
        </div>

      </div>

    </div>
  );
}

export default AdminTicketDetailsPage;
