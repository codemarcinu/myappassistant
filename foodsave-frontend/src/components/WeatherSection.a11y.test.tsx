import '@testing-library/jest-dom';
import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { WeatherSection } from './WeatherSection';

expect.extend(toHaveNoViolations);

describe('WeatherSection accessibility', () => {
  it('has no basic accessibility violations', async () => {
    const { container } = render(<WeatherSection />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
