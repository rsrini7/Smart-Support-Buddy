import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Select, MenuItem } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { BACKEND_API_BASE, STACKOVERFLOW_URL_PATTERN } from '../settings';
import { useNavigate } from 'react-router-dom';

const StackOverflowIngestPage = () => {
  const [stackoverflowUrlsInput, setStackOverflowUrlsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const [augmentMetadata, setAugmentMetadata] = useState(false);
  const [normalizeLanguage, setNormalizeLanguage] = useState(false);
  const [targetLanguage, setTargetLanguage] = useState('en');
  const navigate = useNavigate();
  const theme = useTheme();

  // Accepts comma or newline separated URLs
  const handleUrlChange = (event) => {
    setStackOverflowUrlsInput(event.target.value);
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
    const stackoverflowUrls = stackoverflowUrlsInput
      .split(/[\n,]+/)
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (stackoverflowUrls.length === 0) {
      setError('Please enter at least one Stack Overflow question URL');
      setLoading(false);
      return;
    }

    // Validate URLs: must contain configured STACKOVERFLOW_URL_PATTERN
    const invalidUrls = stackoverflowUrls.filter(url => !url.includes(STACKOVERFLOW_URL_PATTERN));
    if (invalidUrls.length > 0) {
      setError('Only URLs containing "' + STACKOVERFLOW_URL_PATTERN + '" are allowed. Invalid URL(s): ' + invalidUrls.join(', '));
      setLoading(false);
      return;
    }

    const payload = {
      stackoverflow_urls: stackoverflowUrls,
      augment_metadata: augmentMetadata,
      normalize_language: normalizeLanguage,
      target_language: targetLanguage
    };

    try {
      let response = await fetch(`${BACKEND_API_BASE}/ingest-stackoverflow`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // If backend returns 422 or 400, try fallback (backward compatibility)
      if (response.status === 422 || response.status === 400) {
        response = await fetch(`${BACKEND_API_BASE}/ingest-stackoverflow`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ stackoverflow_urls: stackoverflowUrls }),
        });
      }

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
    <Box sx={{ p: 3, backgroundColor: theme.palette.background.default }}>
      <Paper sx={{ p: 4, mb: 4, maxWidth: '70vw', mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Ingest Stack Overflow Q&amp;As
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter one or more Stack Overflow question URLs (comma or newline separated).
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Stack Overflow URLs"
          value={stackoverflowUrlsInput}
          onChange={handleUrlChange}
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
        <Button variant="contained" color="primary" onClick={handleSubmit} disabled={loading}>
          {loading ? <CircularProgress size={24} /> : 'Ingest'}
        </Button>
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mt: 2 }}>Ingest successful!</Alert>}
        {result && (
          <Box sx={{ mt: 2, maxWidth: '100%', overflowX: 'auto', wordBreak: 'break-word', whiteSpace: 'pre-wrap', backgroundColor: theme.palette.background.paper, borderRadius: 2, border: '1px solid', borderColor: theme.palette.divider, p: 2 }}>
            <pre style={{ margin: 0, fontFamily: 'inherit', background: 'none' }}>{JSON.stringify(result, null, 2)}</pre>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default StackOverflowIngestPage;