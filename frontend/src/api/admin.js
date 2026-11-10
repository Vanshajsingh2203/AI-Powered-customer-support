
import api from './axios';

// Fetch all tickets with optional filters and pagination.
export const getAllTickets = async (params = {}) => {
  const response = await api.get('/admin/tickets', {
    params,
  });

  return response.data;
};

// Fetch all agents.
export const getAgents = async () => {
  const response = await api.get('/admin/agents');
  return response.data;
};

// Fetch all customers.
export const getCustomers = async () => {
  const response = await api.get('/admin/customers');
  return response.data;
};

// Fetch all categories.
export const getAdminCategories = async () => {
  const response = await api.get('/admin/categories');
  return response.data;
};


// Create a new support agent.
export const createAgent = async (agentData) => {
  const response = await api.post('/admin/agents', agentData);
  return response.data;
};

// Fetch details of a specific agent.
export const getAgentById = async (agentId) => {
  const response = await api.get(`/admin/agents/${agentId}`);
  return response.data;
};

// Activate or deactivate an agent.
export const updateAgentStatus = async (agentId, isActive) => {
  const response = await api.patch(
    `/admin/agents/${agentId}/status`,
    { is_active: isActive }
  );

  return response.data;
};
