import React, { useEffect } from 'react';
import { FiX } from 'react-icons/fi';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  closeButton?: boolean;
  className?: string;
}

const Modal = React.forwardRef<HTMLDivElement, ModalProps>(
  (
    {
      isOpen,
      onClose,
      title,
      children,
      footer,
      size = 'md',
      closeButton = true,
      className = '',
    },
    ref
  ) => {
    const sizeMap = {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
    };

    // Trap focus and prevent scroll when modal is open
    useEffect(() => {
      if (isOpen) {
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
    }, [isOpen]);

    // Close on Escape key
    useEffect(() => {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape' && isOpen) {
          onClose();
        }
      };

      if (isOpen) {
        document.addEventListener('keydown', handleEscape);
      }

      return () => {
        document.removeEventListener('keydown', handleEscape);
      };
    }, [isOpen, onClose]);

    if (!isOpen) {
      return null;
    }

    return (
      <>
        {/* Backdrop */}
        <div
          className="modal-overlay"
          onClick={onClose}
          role="presentation"
          aria-hidden="true"
        />

        {/* Modal */}
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div
            ref={ref}
            className={`card card-lg w-full ${sizeMap[size]} ${className}`}
          >
            {/* Header */}
            {(title || closeButton) && (
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
                {title && (
                  <h2 id="modal-title" className="text-xl font-bold text-gray-900">
                    {title}
                  </h2>
                )}
                {closeButton && (
                  <button
                    onClick={onClose}
                    className="ml-auto p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close dialog"
                  >
                    <FiX size={24} />
                  </button>
                )}
              </div>
            )}

            {/* Body */}
            <div className="mb-6">{children}</div>

            {/* Footer */}
            {footer && (
              <div className="flex gap-3 justify-end pt-4 border-t border-gray-200">
                {footer}
              </div>
            )}
          </div>
        </div>
      </>
    );
  }
);

Modal.displayName = 'Modal';

export default Modal;
