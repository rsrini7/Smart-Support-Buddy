import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { BACKEND_API_BASE, CONFLUENCE_URL_PATTERN } from '../settings';
import { useNavigate } from 'react-router-dom';

const ConfluenceIngestPage = () => {
  const [confluenceUrlsInput, setConfluenceUrlsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();
  const theme = useTheme();

  // Accepts comma or newline separated URLs
  const handleConfluenceUrlChange = (event) => {
    setConfluenceUrlsInput(event.target.value);
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
    const confluenceUrls = confluenceUrlsInput
      .split(/[\n,]+/)
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (confluenceUrls.length === 0) {
      setError('Please enter at least one Confluence page URLs, separated by commas or new lines');
      setLoading(false);
      return;
    }

    // Validate URLs: must contain configured CONFLUENCE_URL_PATTERN
    const invalidUrls = confluenceUrls.filter(url => !url.includes(CONFLUENCE_URL_PATTERN));
    if (invalidUrls.length > 0) {
      setError('Only URLs containing "' + CONFLUENCE_URL_PATTERN + '" are allowed. Invalid URL(s): ' + invalidUrls.join(', '));
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${BACKEND_API_BASE}/ingest-confluence`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ confluence_urls: confluenceUrls }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to ingest Confluence pages');
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
      <Paper sx={{ p: 4, mb: 4, maxWidth: '70vw', mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Ingest Confluence Pages
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Confluence Page URL to ingest its content into the system.
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Confluence Page URLs"
          variant="outlined"
          value={confluenceUrlsInput}
          onChange={handleConfluenceUrlChange}
          placeholder="Enter one or more Confluence page URLs, separated by commas or new lines"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          color="info"
          onClick={handleSubmit}
          disabled={loading || !confluenceUrlsInput.trim()}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Confluence'}
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
                  URL: {res.confluence_url}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color:
                      theme.palette.mode === 'dark'
                        ? (res.status === 'success'
                            ? theme.palette.success.light
                            : theme.palette.error.light)
                        : (res.status === 'success'
                            ? theme.palette.success.main
                            : theme.palette.error.main),
                    fontWeight: 'bold'
                  }}
                >
                  {res.status === 'success' ? res.message : `Error: ${res.message}`}
                </Typography>
                {res.status === 'success' && res.page_id && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Page ID: {res.page_id}
                  </Typography>
                )}
                {res.status === 'success' && res.page_data && (
                  <pre
                    style={{
                      background: theme.palette.mode === 'dark'
                        ? theme.palette.background.paper
                        : '#f5f5f5',
                      padding: 8,
                      marginTop: 8,
                      fontSize: 12,
                      color: theme.palette.text.primary,
                      maxWidth: '100%',
                      overflowX: 'auto',
                      whiteSpace: 'pre'
                    }}
                  >
                    {JSON.stringify(res.page_data, null, 2)}
                  </pre>
                )}
              </Paper>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default ConfluenceIngestPage;