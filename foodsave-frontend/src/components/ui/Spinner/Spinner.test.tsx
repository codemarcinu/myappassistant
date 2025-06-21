import '@testing-library/jest-dom';
import React from 'react';
import { render } from '@testing-library/react';
import { Spinner } from './index';

describe('Spinner', () => {
  it('renders without crashing', () => {
    const { container } = render(<Spinner />);
    // Sprawdź, czy SVG jest obecny
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('applies correct size class', () => {
    const { container } = render(<Spinner size="lg" />);
    expect(container.firstChild).toHaveClass('w-8 h-8');
  });
});
