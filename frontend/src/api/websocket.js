
import api from './axios';

// Request a short-lived, single-use WebSocket ticket.
// Axios automatically attaches the access token.
export const createWebSocketTicket = async () => {
  const response = await api.post('/ws/ticket');

  return response.data;
};

// Establish a WebSocket connection for a particular ticket.
export const connectToTicketWebSocket = (
  ticketId,
  temporaryTicket
) => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  // Convert HTTP to WS and HTTPS to WSS.
  const wsBaseUrl = apiBaseUrl
    .replace(/^http/, 'ws')
    .replace(/\/+$/, '');

  const wsUrl =
    `${wsBaseUrl}/ws/${ticketId}` +
    `?ticket=${encodeURIComponent(temporaryTicket)}`;

  return new WebSocket(wsUrl);
};
