import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadPage from './UploadPage';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ 
        status: 'success',
        message: 'Upload successful',
        issue_id: 'test-123' 
      }),
    })
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

test('renders UploadPage and submits upload', async () => {
  render(
    <MemoryRouter>
      <UploadPage />
    </MemoryRouter>
  );

  // Initial state check
  expect(screen.getByText('Upload Production Issue')).toBeInTheDocument();
  
  // Check first step content
  expect(screen.getByText(/Select a Microsoft Outlook MSG file/)).toBeInTheDocument();
  
  // Click Next to step 2
  const nextButton = screen.getByRole('button', { name: /next/i });
  await userEvent.click(nextButton);
  
  // Check second step content and fill Jira ticket
  expect(screen.getByText(/Optionally link this issue/)).toBeInTheDocument();
  const jiraInput = screen.getByPlaceholderText(/e\.g\.,?\s*PROD-123/i);
  await userEvent.type(jiraInput, 'PROD-123');
  
  // Move to final step
  await userEvent.click(screen.getByRole('button', { name: /next/i }));
  
  // Check review step content
  expect(screen.getByText(/Review your information/)).toBeInTheDocument();
  
  // Click upload button
  const uploadButton = screen.getByRole('button', { name: /upload and process/i });
  await userEvent.click(uploadButton);
  
  // Wait for success message
  await waitFor(() => {
    expect(screen.getByText(/successfully/i)).toBeInTheDocument();
  });
  
  // Check if view details button appears
  expect(screen.getByRole('button', { name: /view issue details/i })).toBeInTheDocument();
  
  // Verify fetch was called with correct data
  expect(global.fetch).toHaveBeenCalledTimes(1);
  const fetchCall = global.fetch.mock.calls[0];
  expect(fetchCall[0]).toBe('http://localhost:9000/api/upload-msg');
  expect(fetchCall[1].method).toBe('POST');
});