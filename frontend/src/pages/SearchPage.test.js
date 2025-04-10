import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchPage from './SearchPage';
import '@testing-library/jest-dom';

// Mock global fetch
import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve([
          {
            id: '123',
            summary: 'Test Issue',
            description: 'This is a test issue description',
            created_at: '2023-01-01',
            jira_ticket_id: 'PROD-123',
          },
        ]),
    })
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

test('renders SearchPage and performs search', async () => {
  render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>
  );

  // Simulate user typing search query
  const input = screen.getByPlaceholderText(/Enter keywords/i);
  userEvent.type(input, 'error');

  // Simulate pressing Enter or clicking search button
  const button = screen.getByRole('button', { name: /search/i });
  userEvent.click(button);

  // Wait for mocked fetch to resolve and UI to update
  await waitFor(() => {
    expect(screen.getByText(/Test Issue/)).toBeInTheDocument();
  });
});