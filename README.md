# Post-Quantum Messaging App

A full-stack messaging application with post-quantum transport security, featuring real-time messaging, user authentication, and message request system.

## Features

- **User Authentication**: Sign up and login with username/password
- **JWT-based Auth**: Secure token-based authentication stored in httpOnly cookies
- **Post-Quantum Transport Security**: CRYSTALS-Kyber KEM with AES-256-GCM encryption (see [POST_QUANTUM.md](POST_QUANTUM.md))
- **One-to-One Messaging**: Private conversations between users
- **Real-time Updates**: WebSocket-based instant message delivery
- **Message Requests**: First messages require acceptance before conversation starts
- **User Discovery**: Browse and message all registered users

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database with Motor async driver
- **JWT** - Token-based authentication (HS256)
- **Bcrypt** - Password hashing
- **liboqs-python** - Post-quantum cryptography (CRYSTALS-Kyber)
- **WebSockets** - Real-time message delivery

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Web Crypto API** - Client-side encryption

## Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **MongoDB** (local or Atlas)

## Quick Start

### Step 1: Install Prerequisites

1. **Install Python 3.11+**: [python.org](https://www.python.org/downloads/)
2. **Install Node.js 18+**: [nodejs.org](https://nodejs.org/)
3. **Install MongoDB**: Choose one option below

### Step 2: Set Up MongoDB

#### Option A: MongoDB Atlas (Cloud - Recommended)

1. Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create a free cluster (M0 - Free tier)
3. Set up Database Access (create user with password)
4. Set up Network Access (allow from anywhere for development: `0.0.0.0/0`)
5. Get connection string: Click "Connect" → "Connect your application"
6. Copy the connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)

#### Option B: Local MongoDB

1. Download from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install with default settings (includes MongoDB as Windows service)
3. Verify it's running:
   ```powershell
   Get-Service MongoDB
   ```
4. If stopped, start it:
   ```powershell
   Start-Service MongoDB
   ```

#### Option C: Docker

```powershell
docker run -d -p 27017:27017 --name mongodb mongo:7
```

### Step 3: Backend Setup

1. **Navigate to backend directory**:
   ```powershell
   cd PostQuantumMessagingApp\backend
   ```

2. **Create and activate virtual environment**:
   ```powershell
   # Windows
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
   You should see `(venv)` in your prompt.

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Create `.env` file** in the `backend` directory:
   ```powershell
   New-Item .env -ItemType File
   ```

5. **Edit `.env` file** with these contents:
   ```env
   MONGO_URL=mongodb://localhost:27017
   MONGO_DB_NAME=messaging_app
   JWT_SECRET=your-super-secret-jwt-key-change-this-to-something-random-and-long-at-least-32-characters
   ```
   
   **If using MongoDB Atlas**, replace `MONGO_URL`:
   ```env
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
   MONGO_DB_NAME=messaging_app
   JWT_SECRET=your-super-secret-jwt-key-change-this-to-something-random-and-long-at-least-32-characters
   ```
   
   ⚠️ **Important**: `JWT_SECRET` must be at least 32 characters long!

6. **Start the backend server**:
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   Connected to MongoDB: messaging_app
   Application startup complete.
   ```
   
   ✅ Backend is now running at: **http://localhost:8000**  
   📚 API docs available at: **http://localhost:8000/docs**

### Step 4: Frontend Setup

1. **Open a NEW terminal** (keep the backend running) and navigate to frontend:
   ```powershell
   cd PostQuantumMessagingApp\frontend
   ```

2. **Install dependencies**:
   ```powershell
   npm install
   ```

3. **Create `.env` file** (optional, defaults to http://localhost:8000):
   ```powershell
   New-Item .env -ItemType File
   ```
   
   Add to `.env`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the frontend development server**:
   ```powershell
   npm run dev
   ```
   
   You should see:
   ```
   VITE v5.x.x  ready in xxx ms
   ➜  Local:   http://localhost:5173/
   ```
   
   ✅ Frontend is now running at: **http://localhost:5173**

### Step 5: Use the App

1. **Open your browser** and go to: **http://localhost:5173**

2. **Register a new user**:
   - Click "Register"
   - Enter username, password, area code (+1, +44, etc.), and phone number
   - Click "Register"
   - You'll be automatically logged in

3. **Register a second user** (in a different browser window or incognito mode)

4. **Start chatting**:
   - Click any user from the "All Users" section in the sidebar
   - Type a message and send
   - The recipient will see it as a message request
   - After accepting the request, you can chat normally!

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # MongoDB connection
│   │   ├── models.py            # Pydantic models
│   │   ├── auth.py              # Authentication utilities
│   │   ├── pq_transport.py      # Post-quantum transport security
│   │   ├── session_manager.py   # Session key storage
│   │   └── routers/
│   │       ├── auth.py          # Auth endpoints
│   │       ├── messages.py      # Message endpoints
│   │       ├── websocket.py     # WebSocket handler
│   │       └── pq.py            # Post-quantum endpoints
│   ├── requirements.txt
│   └── .env                     # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── context/             # React contexts
│   │   ├── services/            # API client
│   │   ├── utils/               # Utilities (crypto)
│   │   ├── types/               # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── nginx.conf
├── README.md                    # This file
└── POST_QUANTUM.md             # Post-quantum implementation details
```

## Environment Variables

### Backend (`.env` file in `backend/`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGO_URL` | MongoDB connection string | Yes | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | No | `messaging_app` |
| `JWT_SECRET` | Secret key for JWT signing (min 32 chars) | Yes | - |
| `JWT_ALGORITHM` | JWT algorithm | No | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | No | `30` |
| `HOST` | Server host | No | `0.0.0.0` |
| `PORT` | Server port | No | `8000` |

### Frontend (optional `.env` file in `frontend/`)

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_URL` | Backend API URL | No | `http://localhost:8000` |

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
  ```json
  {
    "username": "user123",
    "password": "Password123!",
    "area_code": "+1",
    "phone_number": "1234567890"
  }
  ```

- `POST /auth/login` - Login and get JWT token
  ```json
  {
    "username": "user123",
    "password": "Password123!"
  }
  ```

- `POST /auth/logout` - Logout (clears JWT cookie)
- `GET /auth/me` - Get current user info (requires authentication)
- `GET /auth/users` - Get list of all users (excluding current user)
- `GET /auth/ws-token` - Get WebSocket authentication token

### Messages

- `POST /messages` - Send a message to a specific user
  ```json
  {
    "recipient_id": "user_id_here",
    "content": "Hello!"  // Plaintext format
    // OR
    "recipient_id": "user_id_here",
    "nonce": "base64_nonce",      // Encrypted format
    "ciphertext": "base64_ciphertext"
  }
  ```

- `GET /messages?other_user_id=<user_id>&limit=50` - Get messages from a conversation
- `GET /messages/requests` - Get pending message requests
- `POST /messages/requests/<request_id>/action` - Accept/decline message request
  ```json
  {
    "request_id": "request_id",
    "action": "accept"  // or "decline"
  }
  ```

- `GET /messages/conversations` - Get list of users you've chatted with

### Post-Quantum (see [POST_QUANTUM.md](POST_QUANTUM.md))

- `GET /pq/kem-public-key` - Get server's Kyber public key
- `POST /pq/handshake` - Perform post-quantum handshake

### WebSocket

- `WS /ws/{user_id}?token={jwt_token}` - Real-time message delivery
  - Sends `new_message` events when messages arrive
  - Sends `new_request` events when message requests arrive

## How Messages Work

### Message Flow

```
User A → POST /messages → Server stores in MongoDB → 
Server sends via WebSocket to User B → User B receives instantly
```

All communication goes through the server. Users never communicate directly.

### Message Request System

1. **First Message**: When User A sends the first message to User B, it creates a **message request** (pending state)
2. **Request Notification**: User B sees the request in their sidebar under "Message Requests"
3. **Accept/Decline**: User B can accept or decline the request
4. **After Acceptance**: Future messages go directly to the conversation (no requests needed)

### Database Collections

- `users`: User accounts (username, password_hash, phone_number, etc.)
- `messages`: Accepted messages between users
- `message_requests`: Pending message requests

## Security Features

1. **Password Hashing**: Passwords hashed using bcrypt before storage
2. **JWT Authentication**: Secure token-based authentication with httpOnly cookies
3. **Post-Quantum Transport Security**: CRYSTALS-Kyber KEM with AES-256-GCM encryption (see [POST_QUANTUM.md](POST_QUANTUM.md))
4. **CORS Protection**: Configured CORS middleware for frontend
5. **Rate Limiting**: Applied to login/register endpoints

## Troubleshooting

### Backend Issues

**"Connection refused" or MongoDB errors:**
- Make sure MongoDB is running
- Check your `MONGO_URL` in `.env` is correct
- For Atlas, make sure your IP is whitelisted
- Verify MongoDB service: `Get-Service MongoDB` (Windows)

**"JWT_SECRET must be at least 32 characters":**
- Update your `.env` file with a longer `JWT_SECRET` (at least 32 characters)

**"liboqs not found" warnings:**
- The app will work with fallback mode (see [POST_QUANTUM.md](POST_QUANTUM.md))
- For full post-quantum security, install liboqs (optional)

**Port 8000 already in use:**
- Change the port: `uvicorn app.main:app --reload --port 8001`
- Update frontend `.env` if you have one: `VITE_API_URL=http://localhost:8001`

### Frontend Issues

**"Cannot connect to backend":**
- Make sure backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend `.env` (if you created one)

**"npm install" fails:**
- Make sure Node.js 18+ is installed: `node --version`
- Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

**No users showing in sidebar:**
- Register at least two users
- Users should appear in "All Users" section automatically

### MongoDB Issues

**Check if MongoDB is running:**
```powershell
# Windows - Check service
Get-Service MongoDB

# Check if port is listening
netstat -ano | findstr ":27017"
```

**Test MongoDB connection:**
```powershell
# If mongosh is installed
mongosh
# Type 'exit' to quit
```

## Development Notes

- **Real-time Updates**: WebSocket-based (not polling)
- **JWT Tokens**: Expire after 30 minutes (configurable)
- **Password Requirements**: Minimum 8 characters with uppercase, lowercase, digit, and special character
- **Message Types**: Text only (no file attachments)
- **Chat Type**: One-to-one only (no group chats)

## Deployment

### Deploy to Render / Railway / Fly.io

**Backend:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set environment variables: `MONGO_URL`, `MONGO_DB_NAME`, `JWT_SECRET`

**Frontend:**
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment Variables: `VITE_API_URL=https://your-backend.onrender.com`

## License

MIT
