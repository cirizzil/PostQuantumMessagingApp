# Messaging App

A simple, production-ready full-stack messaging application with encrypted message storage.

## Features

- **User Authentication**: Sign up and login with username/password
- **JWT-based Auth**: Secure token-based authentication
- **Encrypted Messages**: Messages are encrypted at rest using AES-256-GCM
- **Global Chat Room**: Simple one-to-many messaging
- **Real-time Updates**: Polling-based message updates (every 3 seconds)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **JWT** - Token-based authentication
- **Bcrypt** - Password hashing
- **Cryptography** - AES-GCM encryption

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **React Router** - Client-side routing
- **Axios** - HTTP client

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # MongoDB connection
│   │   ├── models.py        # Pydantic models
│   │   ├── auth.py          # Authentication utilities
│   │   ├── encryption.py    # Message encryption/decryption
│   │   └── routers/
│   │       ├── auth.py      # Auth endpoints
│   │       └── messages.py  # Message endpoints
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── context/         # Auth context
│   │   ├── services/        # API client
│   │   ├── types/           # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ and Node.js 18+ (for local development)
- MongoDB (if running locally without Docker)

## Quick Start with Docker

1. **Clone the repository** (or navigate to the project directory)

2. **Generate an encryption key**:
   ```bash
   # Generate a 32-byte key (base64 encoded)
   python -c "import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
   ```
   
   Or use this Python script:
   ```python
   import secrets
   import base64
   print(base64.b64encode(secrets.token_bytes(32)).decode())
   ```

3. **Create a `.env` file** in the root directory:
   ```env
   JWT_SECRET=your-super-secret-jwt-key-change-this
   APP_ENCRYPTION_KEY=<paste-the-generated-key-here>
   ```

4. **Start all services**:
   ```bash
   docker-compose up --build
   ```

5. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Local Development (Without Docker)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and set:
   - `MONGO_URL` - MongoDB connection string (default: `mongodb://localhost:27017`)
   - `JWT_SECRET` - A secret key for JWT signing
   - `APP_ENCRYPTION_KEY` - A 32-byte key (base64 or hex encoded) for message encryption

5. **Start MongoDB** (if not using Docker):
   ```bash
   # Using Docker:
   docker run -d -p 27017:27017 --name mongodb mongo:7
   
   # Or install MongoDB locally
   ```

6. **Run the backend**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Create `.env` file** (optional):
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Run the development server**:
   ```bash
   npm run dev
   ```

5. **Access the app**: http://localhost:5173

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGO_DB_NAME` | Database name | `messaging_app` |
| `JWT_SECRET` | Secret key for JWT signing | Required |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |
| `APP_ENCRYPTION_KEY` | 32-byte encryption key (base64/hex) | Required |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8000` |

## API Endpoints

### Authentication

- `POST /auth/register` - Register a new user
  ```json
  {
    "username": "user123",
    "password": "password123"
  }
  ```

- `POST /auth/login` - Login and get JWT token
  ```json
  {
    "username": "user123",
    "password": "password123"
  }
  ```

- `GET /auth/me` - Get current user info (requires authentication)

### Messages

- `POST /messages` - Send a message (requires authentication)
  ```json
  {
    "content": "Hello, world!"
  }
  ```

- `GET /messages?limit=50` - Get recent messages (requires authentication)

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt before storage
2. **JWT Authentication**: Secure token-based authentication
3. **Message Encryption**: Messages are encrypted at rest using AES-256-GCM
4. **CORS Protection**: Configured CORS middleware for frontend

## Deployment

### Deploy to Render / Railway / Fly.io

1. **Backend Deployment**:
   - Set environment variables in your hosting platform
   - Use MongoDB Atlas or a managed MongoDB service
   - Update `MONGO_URL` to your MongoDB connection string
   - Set `APP_ENCRYPTION_KEY` and `JWT_SECRET`

2. **Frontend Deployment**:
   - Build the frontend: `npm run build`
   - Deploy the `dist` folder to a static hosting service
   - Set `VITE_API_URL` to your backend URL

### Example: Render Deployment

**Backend Service**:
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables: Set all required variables

**Frontend Service**:
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment Variables: `VITE_API_URL=https://your-backend.onrender.com`

## Development Notes

- Messages are polled every 3 seconds (can be changed in `Chat.tsx`)
- JWT tokens expire after 30 minutes (configurable)
- Encryption key must be 32 bytes (256 bits) for AES-256
- MongoDB collections: `users` and `messages`

## Troubleshooting

1. **Connection refused errors**: Ensure MongoDB is running and accessible
2. **Encryption errors**: Verify `APP_ENCRYPTION_KEY` is a valid 32-byte key
3. **CORS errors**: Check that frontend URL is in backend CORS allowed origins
4. **Token expired**: Login again to get a new token

## License

MIT

