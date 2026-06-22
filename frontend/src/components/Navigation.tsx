import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiMessageSquare, FiFileText, FiLogOut, FiMenu, FiX } from 'react-icons/fi';
import { useAuthStore } from '../store/auth';

interface NavigationProps {
  mobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
}

const Navigation = ({ mobileMenuOpen, setMobileMenuOpen }: NavigationProps) => {
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);

  const links = [
    { path: '/', icon: FiHome, label: 'Dashboard' },
    { path: '/conversations', icon: FiMessageSquare, label: 'Conversations' },
    { path: '/documents', icon: FiFileText, label: 'Documents' },
  ];

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
  };

  const handleNavClick = () => {
    // Close mobile menu when navigating
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-gray-900 text-white shadow-lg z-40 flex items-center justify-between px-4">
        <Link to="/" className="flex items-center gap-2" onClick={handleNavClick}>
          <span className="text-xl font-bold">W</span>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold leading-none">WhatsApp AI</h1>
            <p className="text-xs text-gray-400">Assistant</p>
          </div>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
          aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>
      </div>

      {/* Navigation Sidebar */}
      <nav
        className={`
          fixed lg:relative lg:flex
          inset-y-0 left-0 top-16 lg:top-0
          w-64 bg-gray-900 text-white shadow-lg
          flex flex-col h-[calc(100vh-4rem)] lg:h-screen
          transform transition-transform duration-300 ease-in-out
          z-40 lg:z-0
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo Section - Desktop only */}
        <div className="hidden lg:block p-6 border-b border-gray-800">
          <h1 className="text-2xl font-bold tracking-tight">WhatsApp AI</h1>
          <p className="text-gray-400 text-sm mt-1">Assistant</p>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 space-y-2 px-4 py-6 overflow-y-auto">
          {links.map(({ path, icon: Icon, label }) => (
            <Link
              key={path}
              to={path}
              onClick={handleNavClick}
              className={`
                nav-item group
                flex items-center px-4 py-3 rounded-lg
                transition-all duration-200
                ${
                  location.pathname === path
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-gray-300 hover:text-white hover:bg-gray-800'
                }
              `}
              aria-current={location.pathname === path ? 'page' : undefined}
            >
              <Icon className="mr-3 text-lg group-hover:scale-110 transition-transform flex-shrink-0" />
              <span className="font-medium text-sm md:text-base">{label}</span>
            </Link>
          ))}
        </div>

        {/* Logout Button */}
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className={`
              nav-item group
              w-full flex items-center px-4 py-3 rounded-lg
              text-gray-300 hover:text-white hover:bg-gray-800
              transition-all duration-200
            `}
            aria-label="Logout"
          >
            <FiLogOut className="mr-3 text-lg flex-shrink-0" />
            <span className="font-medium text-sm md:text-base">Logout</span>
          </button>
        </div>
      </nav>
    </>
  );
};

export default Navigation;
