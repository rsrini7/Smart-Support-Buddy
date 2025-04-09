import React, { useState } from 'react';
import { Box, Typography, Button, List, ListItem, ListItemText, Alert, CircularProgress } from '@mui/material';

const IngestMsgFilesPage = () => {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFolderSelect = (event) => {
    const selectedFiles = Array.from(event.target.files).filter(file => file.name.endsWith('.msg'));
    setFiles(selectedFiles);
    setResults([]);
    setError('');
  };

  const handleIngest = async () => {
    setLoading(true);
    setError('');
    setResults([]);
    try {
      const response = await fetch('http://localhost:9000/api/ingest-msg-dir', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ directory_path: "/Users/srini/Downloads/msgfiles" }),
      });
      if (!response.ok) {
        throw new Error('Failed to ingest directory');
      }
      const data = await response.json();
      console.log('Ingest directory response:', data);
      if (data.results && Array.isArray(data.results)) {
        setResults(data.results);
      } else {
        setResults([]);
      }
    } catch (err) {
      console.error('Ingest directory error:', err);
      setResults([{ file: 'Directory', status: 'error', error: err.message }]);
    }
    setLoading(false);
  };

  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <Box sx={{ flex: 1 }}>
        <Typography variant="h4" gutterBottom>
          Ingest MSG Files from Folder
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Button variant="contained" component="label">
            Select Folder
            <input
              type="file"
              webkitdirectory="true"
              directory=""
              multiple
              hidden
              onChange={handleFolderSelect}
            />
          </Button>

          <Button variant="contained" onClick={handleIngest} disabled={loading || files.length === 0}>
            {loading ? <CircularProgress size={24} /> : 'Ingest'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

      </Box>

      {files.length > 0 && (
        <Box sx={{ width: 300, maxHeight: 400, overflowY: 'auto', border: '1px solid #ccc', p: 1 }}>
          <Typography variant="subtitle1">Selected Files ({files.length}):</Typography>
          <List dense>
            {files.map((file, index) => (
              <ListItem key={index}>
                <ListItemText primary={file.name} />
              </ListItem>
            ))}
          </List>
        </Box>
      )}


      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {results.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6">Ingestion Results:</Typography>
          <List>
            {results.map((result, index) => (
              <ListItem key={index}>
                <ListItemText
                  primary={result.file}
                  secondary={
                    result.status === 'success'
                      ? `Success - Issue ID: ${result.issue_id ?? 'N/A'}`
                      : `Error: ${result.error}`
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}
    </Box>
  );
};

export default IngestMsgFilesPage;