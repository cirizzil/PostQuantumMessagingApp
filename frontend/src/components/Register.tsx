import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [areaCode, setAreaCode] = useState('+1');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    // Password validation is now handled by backend
    // Frontend validation is just for UX

    setLoading(true);

    // Validate phone number format
    if (!/^\d{7,15}$/.test(phoneNumber)) {
      setError('Phone number must be 7-15 digits');
      setLoading(false);
      return;
    }

    // Validate area code format
    if (!/^\+\d{1,4}$/.test(areaCode)) {
      setError('Area code must start with + followed by 1-4 digits (e.g., +1, +44)');
      setLoading(false);
      return;
    }

    try {
      await authAPI.register({ username, password, area_code: areaCode, phone_number: phoneNumber });
      // Auto-login after registration
      const user = await authAPI.login({ username, password });
      login(user);
      navigate('/chat');
    } catch (err: any) {
      // Handle validation errors from FastAPI/Pydantic
      const errorDetail = err.response?.data?.detail;
      let errorMessage = 'Registration failed. Please try again.';
      
      if (errorDetail) {
        if (Array.isArray(errorDetail)) {
          // Pydantic validation errors are arrays
          errorMessage = errorDetail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else if (typeof errorDetail === 'string') {
          errorMessage = errorDetail;
        } else {
          errorMessage = 'Validation error. Please check your input.';
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>Register</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoComplete="username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              minLength={6}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              minLength={6}
            />
          </div>
          <div className="form-group">
            <label htmlFor="areaCode">Area Code</label>
            <input
              type="text"
              id="areaCode"
              value={areaCode}
              onChange={(e) => setAreaCode(e.target.value)}
              placeholder="+1"
              required
              pattern="^\+\d{1,4}$"
              title="Format: +1, +44, +91, etc."
            />
            <small style={{ color: '#9ca3af', fontSize: '12px', marginTop: '4px', display: 'block' }}>
              Country code (e.g., +1 for USA, +44 for UK)
            </small>
          </div>
          <div className="form-group">
            <label htmlFor="phoneNumber">Phone Number</label>
            <input
              type="text"
              id="phoneNumber"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
              placeholder="1234567890"
              required
              minLength={7}
              maxLength={15}
              pattern="^\d{7,15}$"
              title="7-15 digits only"
            />
            <small style={{ color: '#9ca3af', fontSize: '12px', marginTop: '4px', display: 'block' }}>
              Your phone number (7-15 digits). Share this with others to connect.
            </small>
          </div>
          {error && <div className="error-message">{error}</div>}
          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        <p className="auth-link">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;

