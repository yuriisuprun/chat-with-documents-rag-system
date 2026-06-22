import React from 'react';

export type CardVariant = 'standard' | 'compact' | 'lg';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  interactive?: boolean;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'standard',
      interactive = false,
      loading = false,
      disabled = false,
      className = '',
      onClick,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'card';
    const variantStyles = `card-${variant}`;
    const interactiveStyles = interactive ? 'card-interactive cursor-pointer' : '';
    const loadingStyles = loading ? 'card-loading' : '';
    const disabledStyles = disabled ? 'card-disabled' : '';

    const combinedClassName = [
      baseStyles,
      variantStyles,
      interactiveStyles,
      loadingStyles,
      disabledStyles,
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const handleClick = interactive && !disabled ? onClick : undefined;

    return (
      <div
        ref={ref}
        className={combinedClassName}
        onClick={handleClick}
        role={interactive && !disabled ? 'button' : undefined}
        tabIndex={interactive && !disabled ? 0 : undefined}
        onKeyDown={
          interactive && !disabled
            ? (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleClick?.(e as any);
                }
              }
            : undefined
        }
        aria-disabled={disabled}
        {...props}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/70 rounded">
            <span className="loading-spinner" aria-hidden="true"></span>
          </div>
        )}
        {props.children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export default Card;
