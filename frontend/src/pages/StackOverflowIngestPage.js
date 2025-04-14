import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { BACKEND_API_BASE } from '../settings';
import { useNavigate } from 'react-router-dom';

const StackOverflowIngestPage = () => {
  const [stackoverflowUrlsInput, setStackOverflowUrlsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();
  const theme = useTheme();

  // Accepts comma or newline separated URLs
  const handleUrlChange = (event) => {
    setStackOverflowUrlsInput(event.target.value);
    setError('');
    setSuccess(false);
    setResult(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    setResult(null);

    // Split input by comma or newline, trim, and filter out empty
    const stackoverflowUrls = stackoverflowUrlsInput
      .split(/[\n,]+/)
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (stackoverflowUrls.length === 0) {
      setError('Please enter at least one Stack Overflow question URL');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${BACKEND_API_BASE}/ingest-stackoverflow`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stackoverflow_urls: stackoverflowUrls }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to ingest Stack Overflow Q&A');
      }

      setSuccess(true);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 4, mb: 4, maxWidth: 600, mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Ingest Stack Overflow Q&amp;As
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Stack Overflow question URL to ingest its question and answers into the system.
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Stack Overflow Q&A URLs"
          variant="outlined"
          value={stackoverflowUrlsInput}
          onChange={handleUrlChange}
          placeholder="Enter one or more Stack Overflow Q&A URLs, separated by commas or new lines"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          color="info"
          onClick={handleSubmit}
          disabled={loading || !stackoverflowUrlsInput.trim()}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Stack Overflow'}
        </Button>
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {success && result && result.results && (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success">Ingestion complete. See results below.</Alert>
            {result.results.map((res, idx) => (
              <Paper
                key={idx}
                sx={{
                  p: 2,
                  mt: 2,
                  backgroundColor: res.status === 'success'
                    ? (theme.palette.mode === 'dark' ? theme.palette.success.dark : '#e8f5e9')
                    : (theme.palette.mode === 'dark' ? theme.palette.error.dark : '#ffebee')
                }}
              >
                <Typography variant="subtitle1">
                  URL: {res.stackoverflow_url}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: res.status === 'success'
                      ? theme.palette.success.main
                      : theme.palette.error.main
                  }}
                >
                  {res.status === 'success' ? res.message : `Error: ${res.message}`}
                </Typography>
                {res.status === 'success' && res.ids && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    IDs: {Array.isArray(res.ids) ? res.ids.join(', ') : res.ids}
                  </Typography>
                )}
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default StackOverflowIngestPage;