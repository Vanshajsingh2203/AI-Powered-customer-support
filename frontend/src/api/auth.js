
import api from './axios';

// Register a new customer.
export const registerUser = async (userData) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

// Login an existing user.
export const loginUser = async (credentials) => {
  const response = await api.post('/auth/login', credentials);
  return response.data;
};

// Exchange the refresh token for new tokens.
export const refreshTokens = async (refreshToken) => {
  const response = await api.post('/auth/refresh', {
    refresh_token: refreshToken,
  });

  return response.data;
};

// Logout the current user.
export const logoutUser = async (refreshToken) => {
  const response = await api.post('/auth/logout', {
    refresh_token: refreshToken,
  });

  return response.data;
};
