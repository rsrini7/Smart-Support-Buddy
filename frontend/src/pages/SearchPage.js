import React, { useState, useEffect } from 'react';
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
  Chip,
  Tabs,
  Tab
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';

const SearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize state from location if available
  const [queryText, setQueryText] = useState(location.state?.searchQuery || '');
  const [jiraTicketId, setJiraTicketId] = useState(location.state?.searchJiraId || '');
  const [issueResults, setIssueResults] = useState(location.state?.searchResults || []);
  const [confluenceResults, setConfluenceResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(0);

  useEffect(() => {
    // Perform search if we have initial search parameters
    if (location.state?.searchQuery || location.state?.searchJiraId) {
      handleSearch();
    }
    // eslint-disable-next-line
  }, []); // Run once on mount

  const handleQueryChange = (event) => {
    setQueryText(event.target.value);
    setError('');
  };

  const handleJiraTicketChange = (event) => {
    setJiraTicketId(event.target.value);
    setError('');
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  const handleSearch = async () => {
    if (!queryText && !jiraTicketId) {
      setError('Please enter a search query or Jira ticket ID');
      return;
    }

    setLoading(true);
    setError('');
    setIssueResults([]);
    setConfluenceResults([]);

    // Search issues
    let issues = [];
    let confluence = [];
    let issueError = '';
    let confluenceError = '';

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

      issues = data;
    } catch (err) {
      issueError = err.message;
    }

    // Search confluence
    try {
      const response = await fetch('http://localhost:9000/api/search-confluence', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: queryText,
          limit: 10
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Confluence search failed');
      }

      confluence = data.results || [];
    } catch (err) {
      confluenceError = err.message;
    }

    setIssueResults(issues);
    setConfluenceResults(confluence);

    if (issueError && confluenceError) {
      setError(`Issues: ${issueError} | Confluence: ${confluenceError}`);
    } else if (issueError) {
      setError(`Issues: ${issueError}`);
    } else if (confluenceError) {
      setError(`Confluence: ${confluenceError}`);
    }

    setLoading(false);
  };

  const handleViewIssue = (issueId) => {
    navigate(`/issues/${issueId}`, {
      state: {
        searchResults: issueResults,
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
    if (event.key === 'Enter' && (queryText || jiraTicketId)) {
      handleSearch();
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Search Support Issues / Queries
      </Typography>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" gutterBottom>
          Search for support issues / queries by description or Jira ticket ID. Confluence results are shown in a separate tab.
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

      <Tabs value={tab} onChange={handleTabChange} sx={{ mb: 2 }}>
        <Tab label="Issues" />
        <Tab label="Confluence" />
      </Tabs>

      {/* Issues Tab */}
      {tab === 0 && (
        issueResults.length > 0 ? (
          <Box>
            <Typography variant="h5" gutterBottom>
              Issue Results ({issueResults.length})
            </Typography>
            <Grid container spacing={3}>
              {issueResults.map((issue) => (
                <Grid item xs={12} key={issue.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {issue.title || issue.summary}
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
                        {issue.similarity_score !== undefined && (
                          <Chip
                            label={`Similarity: ${(issue.similarity_score * 100).toFixed(2)}%`}
                            color="secondary"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        <Typography variant="body2" color="text.secondary">
                          Received: {formatDate(issue.received_date || issue.created_at)}
                        </Typography>
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {issue.description?.length > 200
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
              {queryText || jiraTicketId ? 'No results found. Try a different search query.' : 'Enter a search query to begin.'}
            </Typography>
          </Paper>
        )
      )}

      {/* Confluence Tab */}
      {tab === 1 && (
        confluenceResults.length > 0 ? (
          <Box>
            <Typography variant="h5" gutterBottom>
              Confluence Results ({confluenceResults.length})
            </Typography>
            <Grid container spacing={3}>
              {confluenceResults.map((page) => (
                <Grid item xs={12} key={page.page_id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {page.title}
                      </Typography>
                      <Box sx={{ display: 'flex', mb: 1 }}>
                        {page.similarity_score !== undefined && (
                          <Chip
                            label={`Similarity: ${(page.similarity_score * 100).toFixed(2)}%`}
                            color="secondary"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        <Typography variant="body2" color="text.secondary">
                          {page.metadata?.confluence_url && (
                            <a href={page.metadata.confluence_url} target="_blank" rel="noopener noreferrer">
                              View Page
                            </a>
                          )}
                        </Typography>
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {page.content?.length > 200
                          ? `${page.content.substring(0, 200)}...`
                          : page.content}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        ) : loading ? null : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1">
              {queryText ? 'No Confluence results found. Try a different search query.' : 'Enter a search query to begin.'}
            </Typography>
          </Paper>
        )
      )}
    </Box>
  );
};

export default SearchPage;