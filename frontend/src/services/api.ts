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

  getConversationPartners: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/messages/conversations');
    return response.data;
  },

  getAllUsers: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/auth/users');
    return response.data;
  },

  getWebSocketToken: async (): Promise<{ token: string; user_id: string }> => {
    const response = await api.get<{ token: string; user_id: string }>('/auth/ws-token');
    return response.data;
  },
};

export const pqAPI = {
  /**
   * Get the server's Kyber public key for PQ handshake
   */
  getKemPublicKey: async (): Promise<{ public_key: string }> => {
    const response = await api.get<{ public_key: string }>('/pq/kem-public-key');
    return response.data;
  },

  /**
   * Perform PQ handshake by sending KEM ciphertext to server
   */
  handshake: async (ciphertext: string): Promise<{ status: string; message: string }> => {
    const response = await api.post<{ status: string; message: string }>('/pq/handshake', {
      ciphertext
    });
    return response.data;
  },
};

export const messagesAPI = {
  /**
   * Send a plaintext message (backward compatibility)
   */
  sendMessage: async (content: string, recipientId: string): Promise<Message> => {
    const response = await api.post<Message>('/messages', { content, recipient_id: recipientId });
    return response.data;
  },

  /**
   * Send an encrypted message (new PQ transport security format)
   */
  sendMessageEncrypted: async (
    recipientId: string,
    nonce: string,
    ciphertext: string
  ): Promise<Message> => {
    const response = await api.post<Message>('/messages', {
      recipient_id: recipientId,
      nonce,
      ciphertext
    });
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

// WebSocket connection helper
export const createWebSocket = (userId: string, token: string): WebSocket => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || 'localhost:8000';
  const wsUrl = `${wsProtocol}//${wsHost}/ws/${userId}?token=${token}`;
  return new WebSocket(wsUrl);
};

export default api;

