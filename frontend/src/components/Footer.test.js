import React from 'react';
import { render, screen } from '@testing-library/react';
import Footer from './Footer';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

test('renders Footer component', () => {
  render(
    <MemoryRouter>
      <Footer />
    </MemoryRouter>
  );

  // Check for footer landmark
  expect(screen.getByRole('contentinfo')).toBeInTheDocument();
});