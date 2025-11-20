import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { messagesAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { Message } from '../types';
import './Chat.css';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchMessages();
    // Poll for new messages every 3 seconds
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchMessages = async () => {
    try {
      const fetchedMessages = await messagesAPI.getMessages(50);
      setMessages(fetchedMessages);
    } catch (err: any) {
      console.error('Failed to fetch messages:', err);
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      }
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setLoading(true);
    setError('');

    try {
      const sentMessage = await messagesAPI.sendMessage(newMessage.trim());
      setMessages((prev) => [...prev, sentMessage]);
      setNewMessage('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Global Chat</h1>
        <div className="user-info">
          <span>Logged in as: <strong>{user?.username}</strong></span>
          <button onClick={() => { logout(); navigate('/login'); }} className="logout-button">
            Logout
          </button>
        </div>
      </div>
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-messages">No messages yet. Be the first to send one!</div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="message">
              <div className="message-header">
                <span className="message-username">{message.username}</span>
                <span className="message-timestamp">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="error-message">{error}</div>}
      <form onSubmit={handleSend} className="message-input-form">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type your message..."
          className="message-input"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !newMessage.trim()} className="send-button">
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default Chat;

