import '@testing-library/jest-dom';
import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ErrorBoundary } from './ErrorBoundary';

expect.extend(toHaveNoViolations);

const ThrowError = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary accessibility', () => {
  it('has no basic accessibility violations in fallback UI', async () => {
    // Wycisz console.error dla testu
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { container } = render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
    jest.restoreAllMocks();
  });
});
