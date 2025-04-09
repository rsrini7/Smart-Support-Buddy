import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  TextField, 
  Button, 
  CircularProgress, 
  Alert,
  Card,
  CardContent,
  CardActions,
  Grid,
  Divider,
  Chip
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
  import { useEffect } from 'react';

const SearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize state from location if available
  const [queryText, setQueryText] = useState(location.state?.searchQuery || '');
  const [jiraTicketId, setJiraTicketId] = useState(location.state?.searchJiraId || '');
  const [results, setResults] = useState(location.state?.searchResults || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    if ((queryText && queryText.trim() !== '') || (jiraTicketId && jiraTicketId.trim() !== '')) {
      handleSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleQueryChange = (event) => {
    setQueryText(event.target.value);
  };

  const handleJiraTicketChange = (event) => {
    setJiraTicketId(event.target.value);
  };

  const handleSearch = async () => {
    if (!queryText && !jiraTicketId) {
      setError('Please enter a search query or Jira ticket ID');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:9000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: queryText,
          jira_ticket_id: jiraTicketId || null,
          limit: 10
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Search failed');
      }
      
      setResults(data);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewIssue = (issueId) => {
    navigate(`/issues/${issueId}`, {
      state: {
        searchResults: results,
        searchQuery: queryText,
        searchJiraId: jiraTicketId
      }
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Search Production Issues
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" gutterBottom>
          Search for production issues by description or Jira ticket ID.
        </Typography>
        
        <Box sx={{ mt: 3 }}>
          <TextField
            fullWidth
            label="Search Query"
            variant="outlined"
            value={queryText}
            onChange={handleQueryChange}
            onKeyPress={handleKeyPress}
            placeholder="Enter keywords or description"
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Jira Ticket ID (Optional)"
            variant="outlined"
            value={jiraTicketId}
            onChange={handleJiraTicketChange}
            onKeyPress={handleKeyPress}
            placeholder="e.g., PROD-123"
            sx={{ mb: 3 }}
          />
          
          <Button
            variant="contained"
            color="primary"
            onClick={handleSearch}
            disabled={loading || (!queryText && !jiraTicketId)}
          >
            {loading ? <CircularProgress size={24} /> : 'Search'}
          </Button>
        </Box>
      </Paper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {results.length > 0 ? (
        <Box>
          <Typography variant="h5" gutterBottom>
            Search Results ({results.length})
          </Typography>
          
          <Grid container spacing={3}>
            {results.map((issue) => (
              <Grid item xs={12} key={issue.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {issue.title}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', mb: 1 }}>
                      {issue.jira_ticket_id && (
                        <Chip 
                          label={issue.jira_ticket_id} 
                          color="primary" 
                          size="small" 
                          sx={{ mr: 1 }}
                        />
                      )}
                      <Chip 
                        label={`Similarity: ${(issue.similarity_score * 100).toFixed(6)}%`}
                        color="secondary" 
                        size="small" 
                        sx={{ mr: 1 }}
                      />
                      <Typography variant="body2" color="text.secondary">
                        Received: {formatDate(issue.received_date)}
                      </Typography>
                    </Box>
                    
                    <Divider sx={{ my: 1 }} />
                    
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      {issue.description.length > 200 
                        ? `${issue.description.substring(0, 200)}...` 
                        : issue.description}
                    </Typography>
                    
                    {issue.root_cause && (
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">Root Cause:</Typography>
                        <Typography variant="body2">
                          {issue.root_cause.length > 100 
                            ? `${issue.root_cause.substring(0, 100)}...` 
                            : issue.root_cause}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>
                  <CardActions>
                    <Button size="small" onClick={() => handleViewIssue(issue.id)}>
                      View Details
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      ) : loading ? null : (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body1">
            No results found. Try a different search query.
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default SearchPage;