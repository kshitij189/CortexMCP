/**
 * Axios instance with JWT interceptor and base URL config.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor: Attach JWT ───
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cortex_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor: Handle 401 ───
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('cortex_token');
      localStorage.removeItem('cortex_user');
      // Only redirect if not already on auth pages
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth API ───
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

// ─── Research API ───
export const researchAPI = {
  start: (data) => api.post('/research/start', data),
  listJobs: (params) => api.get('/research/jobs', { params }),
  getJob: (id) => api.get(`/research/${id}`),
  deleteJob: (id) => api.delete(`/research/${id}`),
  getComparison: (id) => api.get(`/research/${id}/compare`),
};

export default api;
