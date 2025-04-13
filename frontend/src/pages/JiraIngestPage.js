import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const JiraIngestPage = () => {
  const [jiraId, setJiraId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const handleIdChange = (event) => {
    setJiraId(event.target.value);
    setError('');
    setSuccess(false);
    setResult(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    setResult(null);

    if (!jiraId) {
      setError('Please enter a Jira ticket ID');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('http://localhost:9000/api/ingest-jira', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ jira_ticket_id: jiraId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to ingest Jira ticket');
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
          Ingest Jira Ticket
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Jira ticket ID to ingest its details and embed them into the Chroma vector database.
        </Typography>
        <TextField
          fullWidth
          label="Jira Ticket ID"
          variant="outlined"
          value={jiraId}
          onChange={handleIdChange}
          placeholder="e.g. PROJ-123"
          sx={{ mb: 2 }}
        />
        <Button
          variant="contained"
          color="success"
          onClick={handleSubmit}
          disabled={loading || !jiraId}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Jira Ticket'}
        </Button>
        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Jira ticket ingested successfully!
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {result && result.jira_data && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Jira Data: {JSON.stringify(result.jira_data)}
          </Typography>
        )}
      </Paper>
      <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mt: 2 }}>
        Back
      </Button>
    </Box>
  );
};

export default JiraIngestPage;