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
    <nav className="w-64 bg-gray-900 text-white shadow-lg">
      <div className="p-6">
        <h1 className="text-2xl font-bold">WhatsApp AI</h1>
        <p className="text-gray-400 text-sm">Assistant</p>
      </div>

      <div className="space-y-2 px-4">
        {links.map(({ path, icon: Icon, label }) => (
          <Link
            key={path}
            to={path}
            className={`flex items-center px-4 py-3 rounded-lg transition ${
              location.pathname === path
                ? 'bg-blue-600'
                : 'hover:bg-gray-800'
            }`}
          >
            <Icon className="mr-3" />
            <span>{label}</span>
          </Link>
        ))}
      </div>

      <div className="absolute bottom-0 w-64 p-4 border-t border-gray-800">
        <button
          onClick={logout}
          className="flex items-center w-full px-4 py-3 rounded-lg hover:bg-gray-800 transition"
        >
          <FiLogOut className="mr-3" />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default Navigation;
