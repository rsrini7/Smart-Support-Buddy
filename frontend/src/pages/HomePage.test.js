import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from './HomePage';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

test('renders HomePage with expected content', () => {
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  );

  // Example: check for a heading or unique text
  expect(screen.getByRole('heading', { level: 4, name: /Smart Support Buddy/i })).toBeInTheDocument();
});