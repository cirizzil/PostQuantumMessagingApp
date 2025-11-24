import axios from 'axios';
import type { Token, User, Message, MessageRequest, LoginCredentials, RegisterData } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important: enables cookies to be sent
});

export const authAPI = {
  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post<User>('/auth/register', data);
    return response.data;
  },

  login: async (credentials: LoginCredentials): Promise<User> => {
    const response = await api.post<User>('/auth/login', credentials);
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  getAllUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/auth/users');
    return response.data;
  },
};

export const messagesAPI = {
  sendMessage: async (content: string, recipientId: string): Promise<Message> => {
    const response = await api.post<Message>('/messages', { content, recipient_id: recipientId });
    return response.data;
  },

  getMessages: async (otherUserId: string, limit: number = 50): Promise<Message[]> => {
    const response = await api.get<Message[]>(`/messages?other_user_id=${otherUserId}&limit=${limit}`);
    return response.data;
  },

  getMessageRequests: async (): Promise<MessageRequest[]> => {
    const response = await api.get<MessageRequest[]>('/messages/requests');
    return response.data;
  },

  handleMessageRequest: async (requestId: string, action: 'accept' | 'decline'): Promise<void> => {
    await api.post(`/messages/requests/${requestId}/action`, { request_id: requestId, action });
  },
};

export default api;

