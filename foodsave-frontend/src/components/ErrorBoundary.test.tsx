import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ErrorBoundary } from './ErrorBoundary';

// Komponent, który rzuca błąd dla testów
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>Normal component</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    // Wycisz console.error dla testów
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renderuje dzieci gdy nie ma błędu', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Normal component')).toBeInTheDocument();
  });

  it('renderuje fallback UI gdy wystąpi błąd', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
  });
});
