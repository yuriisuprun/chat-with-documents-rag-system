import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import apiClient from '../api/client';
import { useAuthStore } from '../store/auth';
import { FiMail, FiLock } from 'react-icons/fi';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setToken = useAuthStore((state) => state.setToken);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username.trim() || !password.trim()) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.post('/auth/login', {
        username,
        password,
      });

      setToken(response.data.access_token);
      navigate('/');
      toast.success('Logged in successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-600 to-blue-800 p-4 sm:p-6">
      <div className="w-full max-w-md">
        {/* Card */}
        <div className="card card-lg">
          {/* Header */}
          <div className="text-center mb-6 sm:mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 bg-blue-100 rounded-full mb-3 sm:mb-4">
              <span className="text-2xl sm:text-3xl font-bold text-blue-600">W</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-center">WhatsApp AI</h1>
            <p className="text-gray-500 text-center mt-1 sm:mt-2 text-sm sm:text-base">Admin Dashboard</p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4 sm:space-y-5">
            {/* Username Field */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                <FiMail className="inline mr-2" />
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                disabled={loading}
                required
                autoComplete="username"
                aria-label="Username"
                className="text-sm sm:text-base"
              />
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-xs sm:text-sm font-semibold text-gray-700 mb-2">
                <FiLock className="inline mr-2" />
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                disabled={loading}
                required
                autoComplete="current-password"
                aria-label="Password"
                className="text-sm sm:text-base"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full py-3 font-semibold text-base sm:text-lg mt-6"
              aria-busy={loading}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="loading-spinner"></span>
                  <span>Signing in...</span>
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-xs text-gray-500 mt-6">
            Protected admin area. Unauthorized access is prohibited.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
