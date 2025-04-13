import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const StackOverflowIngestPage = () => {
  const [stackoverflowUrl, setStackOverflowUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const handleUrlChange = (event) => {
    setStackOverflowUrl(event.target.value);
    setError('');
    setSuccess(false);
    setResult(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    setResult(null);

    if (!stackoverflowUrl) {
      setError('Please enter a Stack Overflow question URL');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:9000/api/ingest-stackoverflow', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stackoverflow_url: stackoverflowUrl }),
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
        <Typography variant="h5" gutterBottom>
          Ingest Stack Overflow Q&amp;A
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Stack Overflow question URL to ingest its question and answers into the system.
        </Typography>
        <TextField
          fullWidth
          label="Stack Overflow Question URL"
          variant="outlined"
          value={stackoverflowUrl}
          onChange={handleUrlChange}
          placeholder="https://stackoverflow.com/questions/12345678/example-question"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          color="info"
          onClick={handleSubmit}
          disabled={loading || !stackoverflowUrl}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Stack Overflow'}
        </Button>
        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Stack Overflow Q&amp;A ingested successfully!
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {result && result.ids && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Added IDs: {result.ids.join(', ')}
          </Typography>
        )}
      </Paper>
      <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mt: 2 }}>
        Back
      </Button>
    </Box>
  );
};

export default StackOverflowIngestPage;