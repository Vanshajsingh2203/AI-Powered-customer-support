
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

import {
  createWebSocketTicket,
  connectToTicketWebSocket,
} from '../api/websocket';

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

function AgentTicketDetailsPage() {
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

  const [connectionStatus, setConnectionStatus] =
    useState('disconnected');

  // Add a message only if it does not already exist.
  const addMessageIfNew = (newMessage) => {
    setMessages((previousMessages) => {
      const alreadyExists = previousMessages.some(
        (message) => message.id === newMessage.id
      );

      if (alreadyExists) {
        return previousMessages;
      }

      return [...previousMessages, newMessage].sort(
        (a, b) =>
          new Date(a.created_at) - new Date(b.created_at)
      );
    });
  };

  // Load ticket and conversation.
  useEffect(() => {
    let cancelled = false;

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

        if (cancelled) return;

        setTicket(ticketData);
        setMessages(messageData);

        setSelectedStatus(ticketData.status);
        setSelectedPriority(ticketData.priority);
      } catch (err) {
        if (cancelled) return;

        setError(
          err.response?.data?.detail ||
          'Unable to load ticket details.'
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadTicketData();

    return () => {
      cancelled = true;
    };
  }, [ticketId]);

  // Establish a WebSocket connection for real-time messages.
  useEffect(() => {
    if (!ticket || !user?.id) {
      return;
    }

    let cancelled = false;
    let socket = null;

    const establishConnection = async () => {
      try {
        setConnectionStatus('connecting');

        // Obtain a short-lived, single-use WebSocket ticket.
        const ticketData = await createWebSocketTicket();

        if (cancelled) return;

        // Connect to this ticket's WebSocket.
        socket = connectToTicketWebSocket(
          ticketId,
          ticketData.ticket
        );

        socket.onopen = async () => {
          if (cancelled) return;

          setConnectionStatus('connected');

          // Refresh history after connection to cover
          // messages sent during the connection process.
          try {
            const latestMessages = await getTicketMessages(
              ticketId,
              {
                limit: 100,
                offset: 0,
              }
            );

            if (cancelled) return;

            setMessages((previousMessages) => {
              const messageMap = new Map();

              previousMessages.forEach((message) => {
                messageMap.set(message.id, message);
              });

              latestMessages.forEach((message) => {
                messageMap.set(message.id, message);
              });

              return Array.from(messageMap.values()).sort(
                (a, b) =>
                  new Date(a.created_at) -
                  new Date(b.created_at)
              );
            });
          } catch (err) {
            console.error(
              'Failed to refresh message history:',
              err
            );
          }
        };

        // Receive public messages and internal notes.
        socket.onmessage = (event) => {
          try {
            const incomingData = JSON.parse(event.data);

            // Ignore connection confirmations and other
            // objects that are not actual ticket messages.
            if (
              !incomingData.id ||
              !incomingData.sender_id ||
              typeof incomingData.content !== 'string'
            ) {
              return;
            }

            // Agents are allowed to receive both public
            // messages and internal notes.
            addMessageIfNew(incomingData);

          } catch (err) {
            console.error(
              'Failed to process WebSocket message:',
              err
            );
          }
        };

        socket.onclose = () => {
          if (!cancelled) {
            setConnectionStatus('disconnected');
          }
        };

        socket.onerror = (err) => {
          console.error('WebSocket connection error:', err);
          setConnectionStatus('disconnected');
        };

      } catch (err) {
        if (cancelled) return;

        console.error(
          'Failed to establish WebSocket connection:',
          err
        );

        setConnectionStatus('disconnected');
      }
    };

    establishConnection();

    // Close the connection when leaving the page
    // or switching to another ticket.
    return () => {
      cancelled = true;

      if (socket) {
        socket.close();
      }
    };
  }, [ticketId, ticket, user?.id]);

  // Send a public reply or internal note.
  const handleSendMessage = async (event) => {
    event.preventDefault();

    const content = newMessage.trim();

    if (!content || sending) {
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

      // Add the HTTP response immediately.
      // WebSocket delivery of the same message will
      // be ignored because its ID already exists.
      addMessageIfNew(sentMessage);

      setNewMessage('');

      setSuccess(
        activeTab === 'INTERNAL'
          ? 'Internal note added successfully.'
          : 'Public reply sent successfully.'
      );
    } catch (err) {
      console.error('Failed to send message:', err);

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
          Back to Agent Dashboard
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
          to="/agent/dashboard"
          className="text-decoration-none"
        >
          &larr; Back to Agent Dashboard
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

            <div className="col-md-4">
              <strong>Customer</strong>
              <p>{ticket.customer_name || 'Not available'}</p>
            </div>

            <div className="col-md-4">
              <strong>Category</strong>
              <p>{ticket.category_name || 'Uncategorized'}</p>
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
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">

            <h5 className="mb-1">Ticket Conversation</h5>

            <small
              className={
                connectionStatus === 'connected'
                  ? 'text-success'
                  : connectionStatus === 'connecting'
                    ? 'text-warning'
                    : 'text-danger'
              }
            >
              <span className="me-1">●</span>

              {connectionStatus === 'connected'
                ? 'Live connection'
                : connectionStatus === 'connecting'
                  ? 'Connecting...'
                  : 'Live connection unavailable'}
            </small>

          </div>

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

export default AgentTicketDetailsPage;
