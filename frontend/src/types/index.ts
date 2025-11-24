export interface User {
  id: string;
  username: string;
  created_at: string;
}

export interface Message {
  id: string;
  username: string;
  content: string;
  timestamp: string;
  sender_id: string;
  recipient_id: string;
}

export interface MessageRequest {
  id: string;
  sender_id: string;
  sender_username: string;
  recipient_id: string;
  content: string;
  timestamp: string;
  status: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
  area_code: string;
  phone_number: string;
}

