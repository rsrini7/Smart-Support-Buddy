import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Select, MenuItem } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { BACKEND_API_BASE } from '../settings';

const JiraIngestPage = () => {
  const [jiraIdsInput, setJiraIdsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const [augmentMetadata, setAugmentMetadata] = useState(true);
  const [normalizeLanguage, setNormalizeLanguage] = useState(true);
  const [targetLanguage, setTargetLanguage] = useState('en');
  const navigate = useNavigate();
  const theme = useTheme();

  // Accepts comma or newline separated IDs
  const handleIdChange = (event) => {
    setJiraIdsInput(event.target.value);
    setError('');
    setSuccess(false);
    setResult(null);
  };

  // Backward compatible: if backend does not support new fields, fallback to old payload
  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    setSuccess(false);
    setResult(null);

    // Split input by comma or newline, trim, and filter out empty
    const jiraIds = jiraIdsInput
      .split(/[\n,]+/)
      .map(id => id.trim())
      .filter(id => id.length > 0);

    if (jiraIds.length === 0) {
      setError('Please enter at least one Jira ticket ID');
      setLoading(false);
      return;
    }

    const payload = {
      jira_ticket_ids: jiraIds,
      augment_metadata: augmentMetadata,
      normalize_language: normalizeLanguage,
      target_language: targetLanguage
    };

    try {
      let response = await fetch(`${BACKEND_API_BASE}/ingest-jira`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // If backend returns 422 or 400, try fallback (backward compatibility)
      if (response.status === 422 || response.status === 400) {
        response = await fetch(`${BACKEND_API_BASE}/ingest-jira`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ jira_ticket_ids: jiraIds }),
        });
      }

      const data = await response.json();

      if (!response.ok) {
        // If backend returns a detail string, show it; else show generic error
        throw new Error(data.detail || 'Failed to ingest Jira tickets');
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
          Ingest Jira Tickets
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter the Jira ticket ID to ingest its details and embed them into the Chroma vector database.
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Jira Ticket IDs"
          variant="outlined"
          value={jiraIdsInput}
          onChange={handleIdChange}
          placeholder="Enter one or more Jira ticket IDs, separated by commas or new lines"
          sx={{ mb: 2 }}
        />
        <FormGroup row sx={{ mb: 2 }}>
          <FormControlLabel
            control={<Checkbox checked={augmentMetadata} onChange={e => setAugmentMetadata(e.target.checked)} />}
            label="Extract Metadata"
          />
          <FormControlLabel
            control={<Checkbox checked={normalizeLanguage} onChange={e => setNormalizeLanguage(e.target.checked)} />}
            label="Normalize Language"
          />
          <Select
            value={targetLanguage}
            onChange={e => setTargetLanguage(e.target.value)}
            displayEmpty
            sx={{ minWidth: 120, ml: 2 }}
          >
            <MenuItem value="en">English</MenuItem>
            <MenuItem value="fr">French</MenuItem>
            <MenuItem value="de">German</MenuItem>
            <MenuItem value="es">Spanish</MenuItem>
            <MenuItem value="zh">Chinese</MenuItem>
            {/* Add more languages as needed */}
          </Select>
        </FormGroup>
        <Button
          variant="contained"
          color="success"
          onClick={handleSubmit}
          disabled={loading || !jiraIdsInput.trim()}
        >
          {loading ? <CircularProgress size={24} /> : 'Ingest Jira Tickets'}
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
                  Jira ID: {res.jira_ticket_id}
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
                {res.status === 'success' && res.jira_data && (
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
                    {JSON.stringify(res.jira_data, null, 2)}
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

export default JiraIngestPage;