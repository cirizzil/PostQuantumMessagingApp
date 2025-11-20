import axios from 'axios';
import type { Token, User, Message, LoginCredentials, RegisterData } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  login: async (credentials: LoginCredentials): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', credentials);
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
};

export const messagesAPI = {
  sendMessage: async (content: string): Promise<Message> => {
    const response = await api.post<Message>('/messages', { content });
    return response.data;
  },

  getMessages: async (limit: number = 50): Promise<Message[]> => {
    const response = await api.get<Message[]>(`/messages?limit=${limit}`);
    return response.data;
  },
};

export default api;

