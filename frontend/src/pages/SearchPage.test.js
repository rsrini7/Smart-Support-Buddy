import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchPage from './SearchPage';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

// Mock global fetch
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

const renderSearchPage = (initialState = {}) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/search', state: initialState }]}>
      <SearchPage />
    </MemoryRouter>
  );
};

test('renders SearchPage with empty state', () => {
  renderSearchPage();
  
  expect(screen.getByText(/Search Production Issues/i)).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/Enter keywords/i)).toBeInTheDocument();
  expect(screen.getByPlaceholderText(/e\.g\., PROD-123/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
});

test('renders SearchPage and performs search', async () => {
  renderSearchPage();

  // Simulate user typing search query
  const input = screen.getByPlaceholderText(/Enter keywords/i);
  await userEvent.type(input, 'error');

  // Simulate pressing Enter or clicking search button
  const button = screen.getByRole('button', { name: /search/i });
  await userEvent.click(button);

  // Wait for mocked fetch to resolve and UI to update
  await waitFor(() => {
    expect(screen.getByText(/Test Issue/)).toBeInTheDocument();
  });

  // Verify API call
  expect(global.fetch).toHaveBeenCalledWith(
    expect.any(String),
    expect.objectContaining({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: expect.stringContaining('error'),
    })
  );
});

test('handles API error gracefully', async () => {
  // Mock fetch to return an error
  global.fetch.mockImplementationOnce(() =>
    Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ detail: 'API Error' }),
    })
  );

  renderSearchPage();
  
  const input = screen.getByPlaceholderText(/Enter keywords/i);
  await userEvent.type(input, 'error');
  
  const button = screen.getByRole('button', { name: /search/i });
  await userEvent.click(button);

  // Wait for error message
  await waitFor(() => {
    expect(screen.getByText(/API Error/i)).toBeInTheDocument();
  });
});

test('performs search with Jira ticket ID', async () => {
  renderSearchPage();
  
  const jiraInput = screen.getByPlaceholderText(/e\.g\., PROD-123/i);
  await userEvent.type(jiraInput, 'PROD-123');
  
  const button = screen.getByRole('button', { name: /search/i });
  await userEvent.click(button);

  await waitFor(() => {
    expect(screen.getByText(/Test Issue/)).toBeInTheDocument();
  });

  expect(global.fetch).toHaveBeenCalledWith(
    expect.any(String),
    expect.objectContaining({
      body: expect.stringContaining('PROD-123'),
    })
  );
});

test('disables search button without input', () => {
  renderSearchPage();
  
  const button = screen.getByRole('button', { name: /search/i });
  expect(button).toBeDisabled();
});

test('preserves search state when navigating back', () => {
  const initialState = {
    searchQuery: 'test query',
    searchJiraId: 'PROD-123',
    searchResults: [{
      id: '123',
      title: 'Previous Result',
      description: 'Previous search result',
      created_at: '2023-01-01',
      jira_ticket_id: 'PROD-123',
    }]
  };

  renderSearchPage(initialState);

  expect(screen.getByDisplayValue('test query')).toBeInTheDocument();
  expect(screen.getByDisplayValue('PROD-123')).toBeInTheDocument();
  expect(screen.getByText('Previous Result')).toBeInTheDocument();
});