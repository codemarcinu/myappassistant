import '@testing-library/jest-dom';
import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { Button } from './index';

describe('Button', () => {
  it('renders with children', () => {
    const { getByRole } = render(<Button>Click me</Button>);
    expect(getByRole('button')).toHaveTextContent('Click me');
  });

  it('calls onClick when clicked', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(<Button onClick={handleClick}>Click</Button>);
    fireEvent.click(getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when disabled prop is set', () => {
    const { getByRole } = render(<Button disabled>Disabled</Button>);
    expect(getByRole('button')).toBeDisabled();
  });
});
