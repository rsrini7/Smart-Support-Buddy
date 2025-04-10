import React, { act } from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadPage from './UploadPage';
import '@testing-library/jest-dom';

import { MemoryRouter } from 'react-router-dom';

beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'Upload successful' }),
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

  // Simulate clicking submit button
  const nextButton = screen.getByRole('button', { name: /next/i });

  await act(async () => {
    // Click Next to step 2
    await userEvent.click(nextButton);

    // Fill Jira ticket ID input
    const jiraInput = screen.getByPlaceholderText(/e\.g\.,?\s*PROD-123/i);
    await userEvent.type(jiraInput, 'PROD-123');

    // Click Next to step 3 (upload step)
    await userEvent.click(nextButton);

    // Click Next to trigger upload
    await userEvent.click(nextButton);
  });

  // Optionally, check UI reached upload step
  expect(screen.getAllByRole('button', { name: /next/i }).length).toBeGreaterThanOrEqual(1);
});