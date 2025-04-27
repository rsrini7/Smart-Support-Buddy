import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress, Alert, FormGroup, FormControlLabel, Checkbox, Select, MenuItem } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { BACKEND_API_BASE, CONFLUENCE_URL_PATTERN } from '../settings';
import { useNavigate } from 'react-router-dom';

const ConfluenceIngestPage = () => {
  const [confluenceUrlsInput, setConfluenceUrlsInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [result, setResult] = useState(null);
  const [augmentMetadata, setAugmentMetadata] = useState(true);
  const [normalizeLanguage, setNormalizeLanguage] = useState(true);
  const [targetLanguage, setTargetLanguage] = useState('en');
  const navigate = useNavigate();
  const theme = useTheme();

  // Accepts comma or newline separated URLs
  const handleConfluenceUrlChange = (event) => {
    setConfluenceUrlsInput(event.target.value);
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

    const payload = {
      confluence_urls: confluenceUrls,
      augment_metadata: augmentMetadata,
      normalize_language: normalizeLanguage,
      target_language: targetLanguage
    };

    try {
      let response = await fetch(`${BACKEND_API_BASE}/ingest-confluence`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // If backend returns 422 or 400, try fallback (backward compatibility)
      if (response.status === 422 || response.status === 400) {
        response = await fetch(`${BACKEND_API_BASE}/ingest-confluence`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ confluence_urls: confluenceUrls }),
        });
      }

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
    <Box sx={{ backgroundColor: theme.palette.background.default }}>
      <Paper sx={{ p: 4, mb: 4, maxWidth: '70vw', mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Ingest Confluence Pages
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Enter one or more Confluence page URLs (comma or newline separated).
        </Typography>
        <TextField
          fullWidth
          multiline
          minRows={3}
          label="Confluence URLs"
          value={confluenceUrlsInput}
          onChange={handleConfluenceUrlChange}
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
        {result && <Box sx={{ mt: 2 }}><pre>{JSON.stringify(result, null, 2)}</pre></Box>}
      </Paper>
    </Box>
  );
};

export default ConfluenceIngestPage;