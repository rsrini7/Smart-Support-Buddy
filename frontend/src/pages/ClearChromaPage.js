import React, { useState } from 'react';
import { Box, Typography, Paper, Button, CircularProgress, Alert, Grid } from '@mui/material';
import { BACKEND_API_BASE } from '../settings';

const COLLECTIONS = [
  { name: 'issues', label: 'Issues' },
  { name: 'stackoverflow_qa', label: 'Stack Overflow Q&A' },
  { name: 'confluence_pages', label: 'Confluence Pages' },
];

const ClearChromaPage = () => {
  const [loading, setLoading] = useState({});
  const [success, setSuccess] = useState({});
  const [error, setError] = useState({});

  const handleClear = async (collection) => {
    if (!window.confirm(`Are you sure you want to clear all data from "${collection.label}"? This cannot be undone.`)) return;
    setLoading((prev) => ({ ...prev, [collection.name]: true }));
    setSuccess((prev) => ({ ...prev, [collection.name]: false }));
    setError((prev) => ({ ...prev, [collection.name]: '' }));

    try {
      const response = await fetch(`${BACKEND_API_BASE}/chroma-clear/${collection.name}`, {
        method: 'DELETE',
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to clear collection');
      }
      setSuccess((prev) => ({ ...prev, [collection.name]: true }));
    } catch (err) {
      setError((prev) => ({ ...prev, [collection.name]: err.message }));
    } finally {
      setLoading((prev) => ({ ...prev, [collection.name]: false }));
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 4, mb: 4, maxWidth: 600, mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => window.history.back()} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Clear ChromaDB Collections
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Use the buttons below to clear all data from individual ChromaDB collections.
        </Typography>
        <Grid container spacing={3}>
          {COLLECTIONS.map((collection) => (
            <Grid item xs={12} key={collection.name}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography sx={{ flexGrow: 1 }}>{collection.label}</Typography>
                <Button
                  variant="contained"
                  color="error"
                  onClick={() => handleClear(collection)}
                  disabled={loading[collection.name]}
                >
                  {loading[collection.name] ? <CircularProgress size={20} /> : 'Clear'}
                </Button>
              </Box>
              {success[collection.name] && (
                <Alert severity="success" sx={{ mt: 1 }}>
                  Cleared successfully!
                </Alert>
              )}
              {error[collection.name] && (
                <Alert severity="error" sx={{ mt: 1 }}>
                  {error[collection.name]}
                </Alert>
              )}
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default ClearChromaPage;