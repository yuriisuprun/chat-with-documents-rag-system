import React from 'react';

export type BadgeColor =
  | 'success'
  | 'error'
  | 'warning'
  | 'info'
  | 'gray'
  | 'primary';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  color?: BadgeColor;
  size?: BadgeSize;
  children: React.ReactNode;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    { color = 'gray', size = 'md', className = '', children, ...props },
    ref
  ) => {
    const baseStyles = 'badge';
    const colorStyles = `badge-${color}`;
    const sizeStyles = size !== 'md' ? `badge-${size}` : '';

    const combinedClassName = [baseStyles, colorStyles, sizeStyles, className]
      .filter(Boolean)
      .join(' ');

    return (
      <span ref={ref} className={combinedClassName} {...props}>
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
