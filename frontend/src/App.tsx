import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import Conversations from './pages/Conversations';
import Documents from './pages/Documents';
import Login from './pages/Login';
import { useAuthStore } from './store/auth';

function AppContent() {
  const { isAuthenticated, token } = useAuthStore();

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Navigation />
      <main className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/conversations" element={<Conversations />} />
          <Route path="/documents" element={<Documents />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={8}
        containerClassName="toast-container"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#000',
            borderRadius: '0.5rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          },
          success: {
            style: {
              background: '#ecfdf5',
              color: '#065f46',
            },
            iconTheme: {
              primary: '#10b981',
              secondary: '#ecfdf5',
            },
          },
          error: {
            style: {
              background: '#fef2f2',
              color: '#7f1d1d',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fef2f2',
            },
          },
        }}
      />
    </Router>
  );
}

export default App;
