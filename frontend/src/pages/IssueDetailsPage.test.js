import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import IssueDetailsPage from './IssueDetailsPage';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ id: '123', summary: 'Test Issue' }),
    })
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

test('renders IssueDetailsPage and fetches issue details', async () => {
  render(
    <MemoryRouter>
      <IssueDetailsPage />
    </MemoryRouter>
  );

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalled();
  });

  // Example: check for issue summary text
  // expect(screen.getByText(/Test Issue/)).toBeInTheDocument();
});