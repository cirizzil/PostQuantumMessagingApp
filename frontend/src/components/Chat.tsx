import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { messagesAPI, authAPI, createWebSocket } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useSessionKey } from '../context/SessionKeyContext';
import { encryptMessage } from '../utils/crypto';
import type { Message, MessageRequest, User } from '../types';
import './Chat.css';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationPartners, setConversationPartners] = useState<User[]>([]);  // Users you've chatted with
  const [allUsers, setAllUsers] = useState<User[]>([]);  // All registered users
  const [messageRequests, setMessageRequests] = useState<MessageRequest[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loadingUsers, setLoadingUsers] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const selectedUserIdRef = useRef<string | null>(null);
  const { user, logout, isAuthenticated } = useAuth();
  const { sessionKey, hasSessionKey } = useSessionKey();
  const navigate = useNavigate();
  
  // Keep ref in sync with state
  useEffect(() => {
    selectedUserIdRef.current = selectedUserId;
  }, [selectedUserId]);

  useEffect(() => {
    if (!isAuthenticated || !user) {
      navigate('/login');
      return;
    }
    
    // Fetch conversation partners, all users, and requests on initial load
    fetchConversationPartners();
    fetchAllUsers();
    fetchMessageRequests();
    
    // Setup WebSocket connection for real-time updates
    setupWebSocket();
    
    return () => {
      // Cleanup WebSocket on unmount
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [isAuthenticated, user, navigate]);

  useEffect(() => {
    if (selectedUserId) {
      // Fetch messages when a user is selected
      fetchMessages();
    } else {
      setMessages([]);
    }
  }, [selectedUserId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const setupWebSocket = async () => {
    if (!user?.id) return;
    
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Get WebSocket token from API
    let token: string;
    try {
      const tokenData = await authAPI.getWebSocketToken();
      token = tokenData.token;
    } catch (err) {
      console.error('Failed to get WebSocket token:', err);
      return;
    }
    
    try {
      const ws = createWebSocket(user.id, token);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type === 'new_message') {
            const message: Message = data.message;
            console.log('New message via WebSocket:', message);
            
            // Get current selectedUserId from ref (always up-to-date)
            const currentSelectedUserId = selectedUserIdRef.current;
            console.log('Current selectedUserId (from ref):', currentSelectedUserId);
            console.log('Message sender_id:', message.sender_id);
            console.log('Message recipient_id:', message.recipient_id);
            console.log('Current user id:', user?.id);
            
            // Check if message is for current user (they are recipient)
            const isForCurrentUser = message.recipient_id === user?.id;
            
            // Determine which user this message is from/to
            const otherUserId = message.sender_id === user?.id ? message.recipient_id : message.sender_id;
            
            // Check if this message is for the currently selected conversation
            const isCurrentConversation = currentSelectedUserId === otherUserId;
            
            console.log('isForCurrentUser:', isForCurrentUser);
            console.log('isCurrentConversation:', isCurrentConversation);
            console.log('otherUserId:', otherUserId);
            
            // If this conversation is currently open, add the message immediately
            if (isCurrentConversation && currentSelectedUserId) {
              console.log('Message matches current conversation, adding to UI immediately');
              setMessages((prev) => {
                // Avoid duplicates
                if (prev.some(m => m.id === message.id)) {
                  console.log('Message already in list, skipping');
                  return prev;
                }
                console.log('Adding message to current conversation');
                const updated = [...prev, message].sort((a, b) => 
                  new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
                );
                console.log('Updated messages count:', updated.length);
                return updated;
              });
            }
            
            // Always refresh conversation partners (in case it's a new conversation)
            // This ensures the sidebar updates even if conversation isn't open
            if (isForCurrentUser) {
              fetchConversationPartners();
            }
          } else if (data.type === 'new_request') {
            const request: MessageRequest = data.request;
            console.log('New request via WebSocket:', request);
            setMessageRequests((prev) => {
              // Avoid duplicates
              if (prev.some(r => r.id === request.id)) {
                console.log('Request already in list, skipping');
                return prev;
              }
              console.log('Adding new request to list');
              return [request, ...prev];
            });
          } else if (data.type === 'connected') {
            console.log('WebSocket connection confirmed');
          } else if (data.type === 'pong') {
            // Keepalive response
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err, event.data);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (isAuthenticated && user?.id) {
            setupWebSocket();
          }
        }, 3000);
      };
      
      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      wsRef.current = ws;
      
      // Cleanup ping interval on close
      const originalClose = ws.close;
      ws.close = function() {
        clearInterval(pingInterval);
        originalClose.call(this);
      };
      
    } catch (err) {
      console.error('Failed to setup WebSocket:', err);
    }
  };
  
  const fetchConversationPartners = async () => {
    setLoadingUsers(true);
    try {
      const users = await authAPI.getConversationPartners();
      setConversationPartners(users);
    } catch (err: any) {
      console.error('Failed to fetch conversation partners:', err);
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      } else {
        setError('Failed to load conversations. Please refresh the page.');
      }
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchAllUsers = async () => {
    try {
      const users = await authAPI.getAllUsers();
      setAllUsers(users);
    } catch (err: any) {
      console.error('Failed to fetch all users:', err);
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      }
    }
  };

  const fetchMessages = async () => {
    if (!selectedUserId) return;
    try {
      const fetchedMessages = await messagesAPI.getMessages(selectedUserId, 50);
      // Merge fetched messages with any optimistic messages
      // This preserves messages that were sent but haven't appeared in server yet (requests)
      if (fetchedMessages !== undefined && Array.isArray(fetchedMessages)) {
        setMessages((prev) => {
          // Get IDs of messages we already have (optimistic or previously fetched)
          const existingIds = new Set(prev.map(m => m.id));
          const fetchedIds = new Set(fetchedMessages.map(m => m.id));
          
          // Keep optimistic messages that aren't in fetched list yet
          const optimisticOnly = prev.filter(m => !fetchedIds.has(m.id));
          
          // Combine fetched + optimistic, remove duplicates, sort by timestamp
          const combined = [...fetchedMessages, ...optimisticOnly];
          const unique = Array.from(
            new Map(combined.map(m => [m.id, m])).values()
          ).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
          
          return unique;
        });
      }
    } catch (err: any) {
      // Only log non-401 errors
      if (err.response?.status !== 401) {
        console.error('Failed to fetch messages:', err);
        // Don't clear messages on error - keep what we have
      }
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      }
      // Don't set empty array on other errors - keep existing messages
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedUserId) return;

    setLoading(true);
    setError('');
    const messageContent = newMessage.trim();
    setNewMessage(''); // Clear input immediately for better UX

    try {
      // Encrypt message if we have a session key (PQ transport security)
      let sentMessage: Message;
      
      if (hasSessionKey && sessionKey) {
        // Encrypt the message using AES-GCM with the session key
        console.log('[PQ] Encrypting message before sending...');
        const { nonce, ciphertext } = await encryptMessage(sessionKey, messageContent);
        
        // Send encrypted message
        sentMessage = await messagesAPI.sendMessageEncrypted(
          selectedUserId,
          nonce,
          ciphertext
        );
        console.log('[PQ] Encrypted message sent successfully');
      } else {
        // Fallback to plaintext if no session key (backward compatibility)
        console.warn('[PQ] No session key available, sending plaintext message');
        sentMessage = await messagesAPI.sendMessage(messageContent, selectedUserId);
      }
      
      // Check if this is a new conversation BEFORE adding the optimistic message
      const isNewConversation = messages.length === 0;
      
      // Optimistically add the message to the UI immediately
      // This ensures the user sees their message right away
      setMessages((prev) => {
        // Check if message already exists (avoid duplicates)
        if (prev.some(m => m.id === sentMessage.id)) {
          return prev;
        }
        // Add the new message to the end
        return [...prev, sentMessage];
      });
      
      // Wait a bit before refreshing to ensure the message is committed to the database
      // Then refresh messages to get the latest state from server
      setTimeout(async () => {
        try {
          const updatedMessages = await messagesAPI.getMessages(selectedUserId, 50);
          
          // Check if the sent message appears in the messages list
          const messageExists = updatedMessages.some(m => m.id === sentMessage.id);
          
          if (messageExists) {
            // Message exists in server - use server data (has correct order)
            setMessages(updatedMessages);
          } else {
            // Message doesn't exist in server response
            if (isNewConversation) {
              // This is a new conversation - it was created as a request
              // Keep the optimistic message so sender can see what they sent
              // The message will appear properly once the request is accepted
              // Refresh requests to show it (for recipient)
              await fetchMessageRequests();
            } else {
              // We have existing messages, so this should be a regular message
              // Keep the optimistic message - server might just be slow or there's a sync issue
              // The polling will pick it up in the next refresh (every 3 seconds)
            }
          }
        } catch (refreshErr) {
          // If refresh fails, keep the optimistic message
          console.error('Failed to refresh messages:', refreshErr);
        }
      }, 500); // Small delay to ensure database commit
      
    } catch (err: any) {
      // Restore message if sending failed
      setNewMessage(messageContent);
      
      // Handle validation errors from FastAPI/Pydantic
      const errorDetail = err.response?.data?.detail;
      let errorMessage = 'Failed to send message';
      
      if (errorDetail) {
        if (Array.isArray(errorDetail)) {
          // Pydantic validation errors are arrays
          errorMessage = errorDetail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else if (typeof errorDetail === 'string') {
          errorMessage = errorDetail;
        }
      }
      
      setError(errorMessage);
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

  const getSelectedUserName = () => {
    if (!selectedUserId) return null;
    const selectedUser = conversationPartners.find(u => u.id === selectedUserId);
    // Also check message requests
    const requestUser = messageRequests.find(r => r.sender_id === selectedUserId);
    return selectedUser?.username || requestUser?.sender_username || 'Unknown';
  };

  const fetchMessageRequests = async () => {
    try {
      const requests = await messagesAPI.getMessageRequests();
      setMessageRequests(requests || []);
    } catch (err: any) {
      // Only log non-401 errors to avoid spam
      if (err.response?.status !== 401) {
        console.error('Failed to fetch message requests:', err);
      }
      if (err.response?.status === 401) {
        logout();
        navigate('/login');
      }
    }
  };

  const handleRequestAction = async (requestId: string, action: 'accept' | 'decline') => {
    try {
      await messagesAPI.handleMessageRequest(requestId, action);
      
      if (action === 'accept') {
        // Remove from requests
        const request = messageRequests.find(r => r.id === requestId);
        if (request) {
          // Refresh conversation partners to include the accepted user
          await fetchConversationPartners();
          // Auto-select the accepted user
          setSelectedUserId(request.sender_id);
          // Immediately fetch messages to show the accepted message
          setTimeout(() => {
            fetchMessages();
          }, 300);
        }
      }
      
      // Refresh requests
      await fetchMessageRequests();
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail;
      let errorMessage = `Failed to ${action} request`;
      
      if (errorDetail) {
        if (Array.isArray(errorDetail)) {
          errorMessage = errorDetail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else if (typeof errorDetail === 'string') {
          errorMessage = errorDetail;
        }
      }
      
      setError(errorMessage);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="chat-container">
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h2>Users</h2>
          <div className="user-info-sidebar">
            <span>{user?.username}</span>
            <button onClick={() => { logout(); navigate('/login'); }} className="logout-button">
              Logout
            </button>
          </div>
        </div>
        {/* Message Requests Section */}
        {messageRequests.length > 0 && (
          <div style={{ 
            borderBottom: '1px solid #2d3142', 
            paddingBottom: '12px', 
            marginBottom: '12px',
            maxHeight: '300px',
            overflowY: 'auto'
          }}>
            <div style={{ 
              padding: '12px 16px', 
              fontSize: '11px', 
              fontWeight: '600', 
              color: '#9ca3af', 
              textTransform: 'uppercase', 
              letterSpacing: '0.5px',
              position: 'sticky',
              top: 0,
              background: '#1e2128',
              zIndex: 1
            }}>
              Message Requests ({messageRequests.length})
            </div>
            <div style={{ padding: '0 8px' }}>
              {messageRequests.map((request) => (
                <div
                  key={request.id}
                  style={{
                    padding: '12px',
                    margin: '4px 0',
                    background: 'rgba(74, 124, 255, 0.1)',
                    border: '1px solid rgba(74, 124, 255, 0.3)',
                    borderRadius: '8px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                    <div className="user-avatar" style={{ width: '32px', height: '32px', fontSize: '14px', marginRight: '10px' }}>
                      {request.sender_username[0].toUpperCase()}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', color: '#e4e6eb', fontSize: '14px' }}>{request.sender_username}</div>
                      <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>
                        {formatTimestamp(request.timestamp)}
                      </div>
                    </div>
                  </div>
                  <div style={{ fontSize: '13px', color: '#b0b3b8', marginBottom: '10px', paddingLeft: '42px', fontStyle: 'italic' }}>
                    "{request.content.substring(0, 50)}{request.content.length > 50 ? '...' : ''}"
                  </div>
                  <div style={{ display: 'flex', gap: '8px', paddingLeft: '42px' }}>
                    <button
                      onClick={() => handleRequestAction(request.id, 'accept')}
                      style={{
                        flex: 1,
                        padding: '6px 12px',
                        background: 'linear-gradient(135deg, #4a7cff 0%, #5b8cff 100%)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(74, 124, 255, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleRequestAction(request.id, 'decline')}
                      style={{
                        flex: 1,
                        padding: '6px 12px',
                        background: 'rgba(255, 107, 107, 0.2)',
                        color: '#ff6b6b',
                        border: '1px solid rgba(255, 107, 107, 0.3)',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '12px',
                        fontWeight: '600',
                        transition: 'all 0.2s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 107, 107, 0.3)';
                        e.currentTarget.style.borderColor = 'rgba(255, 107, 107, 0.5)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255, 107, 107, 0.2)';
                        e.currentTarget.style.borderColor = 'rgba(255, 107, 107, 0.3)';
                      }}
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <div className="users-list">
          {loadingUsers ? (
            <div className="empty-users">Loading conversations...</div>
          ) : (
            <>
              {/* Show existing conversation partners */}
              {conversationPartners.length > 0 && (
                <div style={{ 
                  padding: '12px 16px', 
                  fontSize: '11px', 
                  fontWeight: '600', 
                  color: '#9ca3af', 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px',
                  borderBottom: '1px solid #2d3142',
                  marginBottom: '8px'
                }}>
                  Conversations ({conversationPartners.length})
                </div>
              )}
              {conversationPartners.map((otherUser) => (
                <div
                  key={otherUser.id}
                  className={`user-item ${selectedUserId === otherUser.id ? 'active' : ''}`}
                  onClick={() => setSelectedUserId(otherUser.id)}
                >
                  <div className="user-avatar">{otherUser.username[0].toUpperCase()}</div>
                  <div className="user-name">{otherUser.username}</div>
                </div>
              ))}
              
              {/* Show all other users who aren't conversation partners yet */}
              {allUsers.length > 0 && (
                <>
                  <div style={{ 
                    padding: '12px 16px', 
                    fontSize: '11px', 
                    fontWeight: '600', 
                    color: '#9ca3af', 
                    textTransform: 'uppercase', 
                    letterSpacing: '0.5px',
                    borderTop: conversationPartners.length > 0 ? '1px solid #2d3142' : 'none',
                    borderBottom: '1px solid #2d3142',
                    marginTop: conversationPartners.length > 0 ? '8px' : '0',
                    marginBottom: '8px'
                  }}>
                    All Users ({allUsers.filter(u => !conversationPartners.some(cp => cp.id === u.id)).length})
                  </div>
                  {allUsers
                    .filter(userItem => !conversationPartners.some(cp => cp.id === userItem.id))
                    .map((otherUser) => (
                      <div
                        key={otherUser.id}
                        className={`user-item ${selectedUserId === otherUser.id ? 'active' : ''}`}
                        onClick={() => setSelectedUserId(otherUser.id)}
                        style={{
                          opacity: 0.8
                        }}
                      >
                        <div className="user-avatar">{otherUser.username[0].toUpperCase()}</div>
                        <div className="user-name">{otherUser.username}</div>
                      </div>
                    ))}
                </>
              )}
              
              {conversationPartners.length === 0 && allUsers.length === 0 && (
                <div className="empty-users">No users found.</div>
              )}
            </>
          )}
        </div>
      </div>
      <div className="chat-main">
        <div className="chat-header">
          <h1>{selectedUserId ? `Chat with ${getSelectedUserName()}` : 'Select a user to start chatting'}</h1>
        </div>
        {selectedUserId ? (
          <>
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="empty-messages">
                  No messages yet. Start the conversation!
                </div>
              ) : (
                messages.map((message) => {
                  const isOwnMessage = message.sender_id === user?.id;
                  return (
                    <div key={message.id} className={`message ${isOwnMessage ? 'own-message' : ''}`}>
                      <div className="message-header">
                        <span className="message-username">{message.username}</span>
                        <span className="message-timestamp">{formatTimestamp(message.timestamp)}</span>
                      </div>
                      <div className="message-content">{message.content}</div>
                    </div>
                  );
                })
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
          </>
        ) : (
          <div className="no-selection">
            <p>Select a user from the sidebar to start a conversation</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;

