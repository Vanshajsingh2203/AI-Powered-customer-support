
import api from './axios';

// Get tickets belonging to the logged-in customer.
export const getCustomerTickets = async (params = {}) => {
  const response = await api.get('/tickets/', {
    params,
  });

  return response.data;
};

// Get details of a particular ticket.
export const getTicketById = async (ticketId) => {
  const response = await api.get(`/tickets/${ticketId}`);

  return response.data;
};

// Create a new support ticket.
export const createTicket = async (ticketData) => {
  const response = await api.post('/tickets/', ticketData);

  return response.data;
};

// Get messages belonging to a ticket.
export const getTicketMessages = async (
  ticketId,
  params = {}
) => {
  const response = await api.get(
    `/tickets/${ticketId}/messages`,
    { params }
  );

  return response.data;
};

// Send a message in a ticket conversation.
export const sendTicketMessage = async (
  ticketId,
  messageData
) => {
  const response = await api.post(
    `/tickets/${ticketId}/messages`,
    messageData
  );

  return response.data;
};
