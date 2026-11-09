
import api from './axios';

// Fetch all available ticket categories.
export const getCategories = async () => {
  const response = await api.get('/categories/');

  return response.data;
};
