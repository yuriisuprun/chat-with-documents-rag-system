import React from 'react';
import { FiAlertCircle, FiCheckCircle, FiInfo, FiAlertTriangle } from 'react-icons/fi';

export type AlertType = 'success' | 'error' | 'warning' | 'info';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: AlertType;
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  dismissible?: boolean;
  onDismiss?: () => void;
  children?: React.ReactNode;
}

const iconMap: Record<AlertType, React.ReactNode> = {
  success: <FiCheckCircle className="w-5 h-5" />,
  error: <FiAlertCircle className="w-5 h-5" />,
  warning: <FiAlertTriangle className="w-5 h-5" />,
  info: <FiInfo className="w-5 h-5" />,
};

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      type = 'info',
      title,
      description,
      icon,
      dismissible = false,
      onDismiss,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    const [isVisible, setIsVisible] = React.useState(true);

    const handleDismiss = () => {
      setIsVisible(false);
      onDismiss?.();
    };

    if (!isVisible && dismissible) {
      return null;
    }

    const baseStyles = 'alert';
    const typeStyles = `alert-${type}`;
    const combinedClassName = [baseStyles, typeStyles, className]
      .filter(Boolean)
      .join(' ');

    return (
      <div ref={ref} className={combinedClassName} role="alert" {...props}>
        {(icon || iconMap[type]) && (
          <div className="alert-icon" aria-hidden="true">
            {icon || iconMap[type]}
          </div>
        )}

        <div className="alert-content">
          {title && <div className="alert-title">{title}</div>}
          {description && <div className="alert-description">{description}</div>}
          {children}
        </div>

        {dismissible && (
          <button
            onClick={handleDismiss}
            className="ml-4 text-gray-400 hover:text-gray-600 flex-shrink-0"
            aria-label="Dismiss alert"
            title="Dismiss"
          >
            ✕
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
