
import api from './axios';

// Fetch all registered customers.
export const getCustomers = async () => {
  const response = await api.get('/admin/customers');
  return response.data;
};

// Fetch details of a specific customer.
export const getCustomerById = async (customerId) => {
  const response = await api.get(
    `/admin/customers/${customerId}`
  );

  return response.data;
};

// Activate or deactivate a customer.
export const updateCustomerStatus = async (
  customerId,
  isActive
) => {
  const response = await api.patch(
    `/admin/customers/${customerId}/status`,
    { is_active: isActive }
  );

  return response.data;
};
