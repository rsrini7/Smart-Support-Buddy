import React, { useState } from 'react';
import { Box, Typography, Button, List, ListItem, ListItemText, Alert, CircularProgress, Paper } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { BACKEND_API_BASE } from '../settings';
import { useNavigate } from 'react-router-dom';

const IngestMsgFilesPage = () => {
  const [files, setFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const theme = useTheme();

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
      const response = await fetch(`${BACKEND_API_BASE}/ingest-msg-dir`, {
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
    <Box>
      <Paper sx={{ p: 4, mb: 4, maxWidth: 600, mx: 'auto', mt: 6 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="h5" gutterBottom>
          Ingest MSG Files from Folder
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          Ingest Microsoft Outlook MSG files and parse them to extract RCA details and save them into the vector database.
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

        {files.length > 0 && (
          <Box sx={{ width: 300, maxHeight: 400, overflowY: 'auto', border: '1px solid #ccc', p: 1, mb: 2 }}>
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

        {results.length > 0 && !error && (
          <Box sx={{ mt: 3 }}>
            <Alert severity="success">Ingestion complete. See results below.</Alert>
            <Typography variant="h6">Ingestion Results:</Typography>
            <List>
              {results.map((result, index) => (
                <Paper
                  key={index}
                  sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: result.status === 'success'
                      ? (theme.palette.mode === 'dark' ? theme.palette.success.dark : '#e8f5e9')
                      : (theme.palette.mode === 'dark' ? theme.palette.error.dark : '#ffebee')
                  }}
                  elevation={2}
                >
                  <ListItem disableGutters>
                    <ListItemText
                      primary={result.file}
                      secondary={
                        <span
                          style={{
                            color: result.status === 'success'
                              ? theme.palette.success.main
                              : theme.palette.error.main
                          }}
                        >
                          {result.status === 'success'
                            ? `Success - Issue ID: ${result.issue_id ?? 'N/A'}`
                            : `Error: ${result.error}`}
                        </span>
                      }
                    />
                  </ListItem>
                  {result.status === 'success' && result.msg_data && (
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
                      {JSON.stringify(result.msg_data, null, 2)}
                    </pre>
                  )}
                </Paper>
              ))}
            </List>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default IngestMsgFilesPage;