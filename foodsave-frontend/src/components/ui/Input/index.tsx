"use client";

interface InputProps {
  className?: string;
  label?: string;
  error?: string;
  helperText?: string;
  id?: string;
  type?: string;
  value?: string | number | readonly string[];
  onChange?: (e: any) => void;
  disabled?: boolean;
  placeholder?: string;
  [key: string]: any;
}

export function Input({
  className,
  label,
  error,
  helperText,
  id,
  ...props
}: InputProps) {
  // Generate a unique ID for the input if not provided
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="space-y-2">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`
          w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500
          ${error ? 'border-red-500' : 'border-gray-300'}
          ${className || ''}
        `}
        aria-invalid={error ? 'true' : 'false'}
        aria-describedby={
          error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
        }
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${inputId}-helper`} className="text-sm text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
}

Input.displayName = 'Input';
