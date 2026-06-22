import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiMessageSquare, FiFileText, FiLogOut } from 'react-icons/fi';
import { useAuthStore } from '../store/auth';

const Navigation = () => {
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);

  const links = [
    { path: '/', icon: FiHome, label: 'Dashboard' },
    { path: '/conversations', icon: FiMessageSquare, label: 'Conversations' },
    { path: '/documents', icon: FiFileText, label: 'Documents' },
  ];

  return (
    <nav className="w-64 bg-gray-900 text-white shadow-lg flex flex-col h-screen">
      {/* Logo Section */}
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-2xl font-bold tracking-tight">WhatsApp AI</h1>
        <p className="text-gray-400 text-sm mt-1">Assistant</p>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 space-y-2 px-4 py-6">
        {links.map(({ path, icon: Icon, label }) => (
          <Link
            key={path}
            to={path}
            className={`nav-item group ${
              location.pathname === path
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-800'
            }`}
            aria-current={location.pathname === path ? 'page' : undefined}
          >
            <Icon className="mr-3 text-lg group-hover:scale-110 transition-transform" />
            <span className="font-medium">{label}</span>
          </Link>
        ))}
      </div>

      {/* Logout Button */}
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={logout}
          className="nav-item w-full text-gray-300 hover:text-white hover:bg-gray-800 justify-start"
          aria-label="Logout"
        >
          <FiLogOut className="mr-3 text-lg" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default Navigation;
