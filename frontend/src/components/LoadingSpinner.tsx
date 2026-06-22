import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  message = 'Loading...',
  fullScreen = false,
  className = '',
}) => {
  const sizeMap = {
    sm: 'w-6 h-6 border-2',
    md: 'w-8 h-8 border-4',
    lg: 'w-12 h-12 border-4',
  };

  const containerClass = fullScreen
    ? 'fixed inset-0 flex items-center justify-center bg-white/80 z-50'
    : 'loading';

  const spinnerClass = `loading-spinner ${sizeMap[size]}`;

  return (
    <div className={`${containerClass} ${className}`}>
      <div className="flex flex-col items-center gap-4">
        <span className={spinnerClass} aria-hidden="true"></span>
        {message && (
          <span className="text-gray-600 text-sm sm:text-base">{message}</span>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
