import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const ConfluenceIngestPage = () => {
  const [confluenceUrl, setConfluenceUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const handleConfluenceUrlChange = (event) => {
    setConfluenceUrl(event.target.value);
    setError('');
    setSuccess(false);
    setResult(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    setResult(null);

    if (!confluenceUrl) {
      setError('Please enter a Confluence page URL');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:9000/api/ingest-confluence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ confluence_url: confluenceUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to ingest Confluence page');
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
        <Typography variant="h5" gutterBottom>
          Ingest Confluence Page
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Confluence Page URL to ingest its content into the system.
        </Typography>
        <TextField
          fullWidth
          label="Confluence Page URL"
          variant="outlined"
          value={confluenceUrl}
          onChange={handleConfluenceUrlChange}
          placeholder="https://confluence.example.com/pages/viewpage.action?pageId=12345"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          color="info"
          onClick={handleSubmit}
          disabled={loading || !confluenceUrl}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Confluence'}
        </Button>
        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Confluence page ingested successfully!
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {result && result.page_id && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Page ID: {result.page_id}
          </Typography>
        )}
      </Paper>
      <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mt: 2 }}>
        Back
      </Button>
    </Box>
  );
};

export default ConfluenceIngestPage;