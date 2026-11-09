
import api from './axios';

// Fetch tickets assigned to the logged-in agent.
export const getAssignedTickets = async (params = {}) => {
  const response = await api.get('/agents/tickets', {
    params,
  });

  return response.data;
};

// Update the status or priority of an assigned ticket.
export const updateAssignedTicket = async (
  ticketId,
  updateData
) => {
  const response = await api.patch(
    `/agents/tickets/${ticketId}`,
    updateData
  );

  return response.data;
};

// Fetch details of a specific ticket.
export const getAgentTicketById = async (ticketId) => {
  const response = await api.get(`/tickets/${ticketId}`);
  return response.data;
};