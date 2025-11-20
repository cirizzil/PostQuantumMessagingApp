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
}

