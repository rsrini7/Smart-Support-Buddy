import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchPage from './SearchPage';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

// Helper: Silence act() deprecation warnings for now
beforeAll(() => {
  jest.spyOn(console, 'error').mockImplementation((msg, ...args) => {
    if (typeof msg === 'string' && msg.includes('ReactDOMTestUtils.act')) return;
    // pass through other errors
    console.warn(msg, ...args);
  });
});
afterAll(() => {
  console.error.mockRestore && console.error.mockRestore();
});

// Mock global fetch
beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () =>
        Promise.resolve({
          results: [
            {
              id: '123',
              summary: 'Test Issue',
              description: 'This is a test issue description',
              created_at: '2023-01-01',
              jira_ticket_id: 'PROD-123',
              type: 'vector_issue',
            },
          ],
        }),
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
  
  expect(screen.getByText(/Search Support Issues \/ Queries/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Search Query/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
});

test('renders SearchPage and performs search', async () => {
  renderSearchPage();

  const input = screen.getByLabelText(/Search Query/i);
  await userEvent.type(input, 'error');

  const button = screen.getByRole('button', { name: /search/i });
  await userEvent.click(button);

  await waitFor(() => {
    expect(screen.getByText(/Test Issue/)).toBeInTheDocument();
  });

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
  global.fetch.mockImplementationOnce(() =>
    Promise.resolve({
      ok: false,
      json: () => Promise.resolve({ detail: 'API Error' }),
    })
  );

  renderSearchPage();
  
  const input = screen.getByLabelText(/Search Query/i);
  await userEvent.type(input, 'error');
  
  const button = screen.getByRole('button', { name: /search/i });
  await userEvent.click(button);

  await waitFor(() => {
    expect(screen.getByText(/API Error/i)).toBeInTheDocument();
  });
});

test('performs search with Jira ticket ID', async () => {
  renderSearchPage();
  
  const input = screen.getByLabelText(/Search Query/i);
  await userEvent.type(input, 'PROD-123');
  
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
      summary: 'Previous Result',
      description: 'Previous search result',
      created_at: '2023-01-01',
      jira_ticket_id: 'PROD-123',
      type: 'vector_issue',
    }]
  };

  renderSearchPage(initialState);

  expect(screen.getByDisplayValue('test query')).toBeInTheDocument();
  expect(screen.getByText(/All Results \(0\)/i)).toBeInTheDocument();
});