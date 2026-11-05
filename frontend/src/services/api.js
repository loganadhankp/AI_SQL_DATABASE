import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercept 401 Unauthorized to trigger logout
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (!window.location.pathname.includes('/login')) {
        window.location.reload();
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
  getMe: () => api.get('/api/auth/me'),
};

export const connectionsAPI = {
  list: () => api.get('/api/connections'),
  test: (data) => api.post('/api/connections/test', data),
  create: (data) => api.post('/api/connections', data),
  delete: (id) => api.delete(`/api/connections/${id}`),
  getSchema: (id) => api.get(`/api/connections/${id}/schema`),
  getTables: (id) => api.get(`/api/connections/${id}/tables`),
  getTablePreview: (id, tableName) => api.get(`/api/connections/${id}/tables/${tableName}`),
};

export const analystAPI = {
  query: (data) => api.post('/api/analyst/query', data),
  getQueryById: (id) => api.get(`/api/analyst/query/${id}`),
  submitFeedback: (id, feedback) => api.post(`/api/analyst/query/${id}/feedback`, feedback),
};

export const historyAPI = {
  list: (limit = 50) => api.get(`/api/history?limit=${limit}`),
  delete: (id) => api.delete(`/api/history/${id}`),
};

export const dashboardAPI = {
  getOverview: () => api.get('/api/dashboard/overview'),
};

export default api;
