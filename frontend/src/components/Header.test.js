import React from 'react';
import { render, screen } from '@testing-library/react';
import Header from './Header';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

test('renders Header component', () => {
  render(
    <MemoryRouter>
      <Header />
    </MemoryRouter>
  );

  // Check for navigation or logo
  expect(screen.getByRole('banner')).toBeInTheDocument();
});