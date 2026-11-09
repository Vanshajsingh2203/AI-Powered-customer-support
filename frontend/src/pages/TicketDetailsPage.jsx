
import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import {
  getTicketById,
  getTicketMessages,
  sendTicketMessage,
} from '../api/tickets';

function TicketDetailsPage() {
  const { ticketId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');

  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  // Load ticket details and conversation history.
  useEffect(() => {
    const fetchTicketDetails = async () => {
      setLoading(true);
      setError('');

      try {
        const [ticketData, messageData] = await Promise.all([
          getTicketById(ticketId),
          getTicketMessages(ticketId, {
            limit: 100,
            offset: 0,
          }),
        ]);

        setTicket(ticketData);
        setMessages(messageData);
      } catch (err) {
        console.error('Failed to load ticket details:', err);

        setError(
          err.response?.data?.detail ||
          'Unable to load this ticket. Please try again.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTicketDetails();
  }, [ticketId]);

  // Send a new message.
  const handleSendMessage = async (event) => {
    event.preventDefault();

    const content = messageInput.trim();

    if (!content || sending) {
      return;
    }

    setSending(true);
    setError('');

    try {
      const newMessage = await sendTicketMessage(ticketId, {
        content,
      });

      setMessages((previousMessages) => [
        ...previousMessages,
        newMessage,
      ]);

      setMessageInput('');
    } catch (err) {
      console.error('Failed to send message:', err);

      setError(
        err.response?.data?.detail ||
        'Unable to send your message. Please try again.'
      );
    } finally {
      setSending(false);
    }
  };

  // Format message timestamps.
  const formatDate = (date) => {
    return new Date(date).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-vh-100 d-flex justify-content-center align-items-center">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="text-muted mt-3">
            Loading ticket details...
          </p>
        </div>
      </div>
    );
  }

  if (error && !ticket) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">
          {error}
        </div>

        <button
          className="btn btn-outline-primary"
          onClick={() => navigate('/customer/dashboard')}
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const isOwnMessage = (message) =>
    message.sender_id === user?.id;

  return (
    <div className="min-vh-100 bg-light">

      {/* Navigation */}
      <nav className="navbar bg-white shadow-sm">
        <div className="container">
          <Link
            to="/customer/dashboard"
            className="navbar-brand fw-bold text-primary fs-4"
          >
            SupportDesk
          </Link>

          <Link
            to="/customer/dashboard"
            className="btn btn-outline-secondary btn-sm"
          >
            Back to Dashboard
          </Link>
        </div>
      </nav>

      <div className="container py-5">

        {/* Ticket information */}
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body p-4">

            <div className="d-flex justify-content-between align-items-start flex-wrap gap-3">

              <div>
                <p className="text-muted small mb-2">
                  Ticket ID: {ticket.id}
                </p>

                <h3 className="fw-bold mb-2">
                  {ticket.title}
                </h3>

                <p className="text-muted mb-3">
                  {ticket.description}
                </p>
              </div>

              <span className="badge bg-primary-subtle text-primary p-2">
                {ticket.status.replaceAll('_', ' ')}
              </span>

            </div>

            <hr />

            <div className="d-flex flex-wrap gap-4">
              <div>
                <small className="text-muted d-block">
                  Category
                </small>
                <strong>
                  {ticket.category_name || 'Uncategorized'}
                </strong>
              </div>

              <div>
                <small className="text-muted d-block">
                  Priority
                </small>
                <strong>{ticket.priority}</strong>
              </div>

              <div>
                <small className="text-muted d-block">
                  Created
                </small>
                <strong>{formatDate(ticket.created_at)}</strong>
              </div>
            </div>

          </div>
        </div>

        {/* Conversation */}
        <div className="card border-0 shadow-sm">
          <div className="card-header bg-white p-4">
            <h5 className="fw-bold mb-0">
              Conversation
            </h5>
            <small className="text-muted">
              Communicate with your support team.
            </small>
          </div>

          <div
            className="card-body p-4"
            style={{ minHeight: '350px' }}
          >

            {error && (
              <div className="alert alert-danger">
                {error}
              </div>
            )}

            {messages.length === 0 ? (
              <div className="text-center text-muted py-5">
                <h6>No messages yet</h6>
                <p className="mb-0">
                  Send a message to start the conversation.
                </p>
              </div>
            ) : (
              <div className="d-flex flex-column gap-4">

                {messages.map((message) => {
                  const ownMessage = isOwnMessage(message);

                  return (
                    <div
                      key={message.id}
                      className={`d-flex ${
                        ownMessage
                          ? 'justify-content-end'
                          : 'justify-content-start'
                      }`}
                    >
                      <div style={{ maxWidth: '75%' }}>

                        <div
                          className={`p-3 rounded-3 ${
                            ownMessage
                              ? 'bg-primary text-white'
                              : 'bg-light border'
                          }`}
                        >
                          {message.content}
                        </div>

                        <small className="text-muted d-block mt-1">
                          {ownMessage ? 'You' : 'Support Team'}
                          {' · '}
                          {formatDate(message.created_at)}
                        </small>

                      </div>
                    </div>
                  );
                })}

              </div>
            )}

          </div>

          {/* Message input */}
          <div className="card-footer bg-white p-4">

            <form
              onSubmit={handleSendMessage}
              className="d-flex gap-2"
            >
              <input
                type="text"
                className="form-control"
                placeholder="Type your message..."
                value={messageInput}
                onChange={(event) =>
                  setMessageInput(event.target.value)
                }
                disabled={sending}
                maxLength={5000}
              />

              <button
                type="submit"
                className="btn btn-primary px-4"
                disabled={sending || !messageInput.trim()}
              >
                {sending ? 'Sending...' : 'Send'}
              </button>
            </form>

            <small className="text-muted d-block mt-2">
              Your messages are visible to the support team.
            </small>

          </div>
        </div>

      </div>
    </div>
  );
}

export default TicketDetailsPage;
