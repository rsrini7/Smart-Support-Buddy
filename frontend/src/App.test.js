import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

test('renders App with Header and Footer', () => {
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>
  );

  // Check for header text or element
  expect(screen.getByRole('banner')).toBeInTheDocument();

  // Check for footer text or element
  expect(screen.getByRole('contentinfo')).toBeInTheDocument();
});