import React from 'react';
import Input, { InputProps } from './Input';

interface FormFieldProps extends Omit<InputProps, 'label'> {
  label: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  hint?: string;
  icon?: React.ReactNode;
}

const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
  (
    {
      label,
      required = false,
      error,
      helperText,
      hint,
      icon,
      containerClassName = '',
      ...inputProps
    },
    ref
  ) => {
    return (
      <div className={`space-y-2 ${containerClassName}`}>
        <label className="block text-sm font-semibold text-gray-700">
          {icon && <span className="inline-block mr-2">{icon}</span>}
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>

        <Input
          ref={ref}
          error={error}
          helperText={helperText}
          required={required}
          {...inputProps}
        />

        {hint && !error && !helperText && (
          <p className="text-xs text-gray-500">{hint}</p>
        )}
      </div>
    );
  }
);

FormField.displayName = 'FormField';

export default FormField;
