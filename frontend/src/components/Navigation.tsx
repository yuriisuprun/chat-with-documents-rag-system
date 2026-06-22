import React, { useEffect } from 'react';
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

  // Lock scroll on mobile when menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
    } else {
      document.body.style.overflow = 'auto';
      document.body.style.position = 'static';
      document.body.style.width = 'auto';
    }

    return () => {
      document.body.style.overflow = 'auto';
      document.body.style.position = 'static';
      document.body.style.width = 'auto';
    };
  }, [mobileMenuOpen]);

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
    setMobileMenuOpen(false);
  };

  return (
    <>
      {/* Mobile Header - Hidden on desktop (lg:hidden) */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-gray-900 text-white shadow-lg z-40 flex items-center justify-between px-4">
        <Link 
          to="/" 
          className="flex items-center gap-2 min-h-[2.75rem] min-w-[2.75rem] justify-center" 
          onClick={handleNavClick}
          aria-label="Home"
        >
          <span className="text-2xl font-bold">W</span>
          <div className="hidden sm:block">
            <h1 className="text-sm font-bold leading-tight">WhatsApp AI</h1>
            <p className="text-xs text-gray-400">Assistant</p>
          </div>
        </Link>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-gray-800 active:bg-gray-700 transition-colors min-h-[2.75rem] min-w-[2.75rem] flex items-center justify-center"
          aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={mobileMenuOpen}
          aria-controls="mobile-nav"
        >
          {mobileMenuOpen ? <FiX size={24} /> : <FiMenu size={24} />}
        </button>
      </div>

      {/* Navigation Sidebar */}
      <nav
        id="mobile-nav"
        className={`
          fixed lg:relative lg:flex
          inset-y-0 left-0 top-16 lg:top-0
          w-64 bg-gray-900 text-white shadow-lg
          flex flex-col h-[calc(100vh-4rem)] lg:h-screen
          transform transition-transform duration-300 ease-in-out
          z-40 lg:z-0
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
        aria-label="Main navigation"
        role="navigation"
      >
        {/* Logo Section - Desktop only */}
        <div className="hidden lg:block p-6 border-b border-gray-800">
          <h1 className="text-2xl font-bold tracking-tight">WhatsApp AI</h1>
          <p className="text-gray-400 text-sm mt-1">Assistant</p>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 space-y-2 px-4 py-6 overflow-y-auto" role="menubar">
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
                    : 'text-gray-300 hover:text-white hover:bg-gray-800 active:bg-gray-700'
                }
              `}
              aria-current={location.pathname === path ? 'page' : undefined}
              role="menuitem"
            >
              <Icon 
                className="mr-3 text-lg group-hover:scale-110 transition-transform flex-shrink-0" 
                aria-hidden="true"
              />
              <span className="font-medium text-sm md:text-base">{label}</span>
            </Link>
          ))}
        </div>

        {/* Logout Button */}
        <div className="p-4 border-t border-gray-800" role="menubar">
          <button
            onClick={handleLogout}
            className={`
              nav-item group
              w-full flex items-center px-4 py-3 rounded-lg
              text-gray-300 hover:text-white hover:bg-gray-800 active:bg-gray-700
              transition-all duration-200
              min-h-[2.75rem]
            `}
            aria-label="Logout from WhatsApp AI"
            role="menuitem"
          >
            <FiLogOut 
              className="mr-3 text-lg flex-shrink-0" 
              aria-hidden="true"
            />
            <span className="font-medium text-sm md:text-base">Logout</span>
          </button>
        </div>
      </nav>

      {/* Mobile menu overlay - Closes menu when clicked */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
          role="presentation"
          aria-hidden="true"
        />
      )}
    </>
  );
};

export default Navigation;
