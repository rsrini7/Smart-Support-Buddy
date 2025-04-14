import React, { useState, useEffect } from 'react';
import { Link } from '@mui/material';
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
import { BACKEND_API_BASE } from '../settings';

const SearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize state from location if available
  const [queryText, setQueryText] = useState(() => location.state?.searchQuery || '');
  const [combinedResults, setCombinedResults] = useState(() => location.state?.searchResults || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(0);
  const [singlePageResult, setSinglePageResult] = useState(false);

  useEffect(() => {
    // Perform search if we have initial search parameters
    if (location.state?.searchQuery) {
      handleSearch();
    }
    // eslint-disable-next-line
  }, []); // Run once on mount

  const handleQueryChange = (event) => {
    setQueryText(event.target.value);
    setError('');
  };

  const handleTabChange = (event, newValue) => {
    setTab(newValue);
  };

  const handleSearch = async () => {
    if (!queryText) {
      setError('Please enter a search query');
      // Do NOT clear results if search is invalid
      return;
    }
    // Only clear results if a valid search is being performed

    setLoading(true);
    setError('');
    setCombinedResults([]);

    try {
      const response = await fetch(`${BACKEND_API_BASE}/search`, {
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
        throw new Error(data.detail || 'Search failed');
      }

      setCombinedResults(data.results || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleViewIssue = (issueId) => {
    navigate(`/issues/${issueId}`, {
      state: {
        searchResults: combinedResults,
        searchQuery: queryText
      }
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && queryText) {
      handleSearch();
    }
  };

  // Helper to get the correct URL for each result type
  function getResultUrl(result) {
    if (result.type === 'confluence') {
      return result.url || result.metadata?.confluence_url;
    }
    if (result.type === 'stackoverflow') {
      return result.url || result.metadata?.url;
    }
    // For issue results (jira/msg), try jira_url, fallback to nothing
    if (result.type === 'jira' || result.type === 'msg' || result.type === 'vector_issue') {
      return result.jira_url || result.url || (result.jira_data && result.jira_data.url) || '';
    }
    return '';
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom color="text.primary">
        Search Support Issues / Queries
      </Typography>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Button variant="outlined" onClick={() => navigate(-1)} sx={{ mb: 2 }}>
          Back
        </Button>
        <Typography variant="body1" gutterBottom>
          Search for support issues / queries by description.
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

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={loading || !queryText}
              sx={{ mr: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Search'}
            </Button>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                id="singlePageResult"
                checked={singlePageResult}
                onChange={(e) => setSinglePageResult(e.target.checked)}
                style={{ marginRight: 6 }}
              />
              <label htmlFor="singlePageResult" style={{ userSelect: 'none' }}>
                Single Page Result
              </label>
            </Box>
          </Box>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {singlePageResult ? (
        <Box>
          <Typography
            variant="h5"
            gutterBottom
            sx={{
              color: (theme) =>
                theme.palette.mode === 'dark'
                  ? theme.palette.text.primary
                  : 'inherit'
            }}
          >
            All Results
          </Typography>
          <Grid container spacing={3}>
            {combinedResults.length > 0 ? (
              combinedResults.map((result, idx) => (
                <Grid item xs={12} key={result.id || idx}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {result.title || result.summary}
                      </Typography>
                      <Box sx={{ display: 'flex', mb: 1, alignItems: 'center' }}>
                        {/* Source tag */}
                        <Chip
                          label={
                            result.type === 'jira' || result.type === 'msg' || result.type === 'vector_issue'
                              ? 'Issue'
                              : result.type.charAt(0).toUpperCase() + result.type.slice(1)
                          }
                          color={
                            result.type === 'jira' || result.type === 'msg' || result.type === 'vector_issue'
                              ? 'primary'
                              : result.type === 'confluence'
                              ? 'info'
                              : 'secondary'
                          }
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        {/* Extra tags */}
                        {result.jira_ticket_id && (
                          <Chip
                            label={result.jira_ticket_id}
                            color="default"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        {typeof result.similarity_score === 'number' && (
                          <Chip
                            label={`Similarity: ${(result.similarity_score * 100).toFixed(2)}%`}
                            color="success"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        {result.type === 'stackoverflow' && (
                          <Chip
                            label={result.soType === 'question' ? 'Question' : 'Answer'}
                            color={result.soType === 'question' ? 'primary' : 'info'}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        {result.description?.length > 200
                          ? `${result.description.substring(0, 200)}...`
                          : result.description}
                      </Typography>
                      {result.root_cause && (
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="subtitle2">Root Cause:</Typography>
                          <Typography variant="body2">
                            {result.root_cause.length > 100
                              ? `${result.root_cause.substring(0, 100)}...`
                              : result.root_cause}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                    <CardActions>
                      {['jira', 'msg', 'vector_issue'].includes(result.type) && (
                        <Button size="small" variant="outlined" onClick={() => handleViewIssue(result.id)}>
                          View Details
                        </Button>
                      )}
                      {getResultUrl(result) && (result.type === 'confluence' || result.type === 'stackoverflow') && (
                        <Button
                          size="small"
                          variant="text"
                          color="primary"
                          href={getResultUrl(result)}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ ml: 1 }}
                        >
                          {result.type === 'confluence' ? 'View Page' : 'View on Stack Overflow'}
                        </Button>
                      )}
                    </CardActions>
                  </Card>
                </Grid>
              ))
            ) : loading ? null : (
              <Grid item xs={12}>
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body1">
                    {queryText
                      ? 'No results found. Try a different search query.'
                      : 'Enter a search query to begin.'}
                  </Typography>
                </Paper>
              </Grid>
            )}
          </Grid>
        </Box>
      ) : (
        <>
          <Tabs value={tab} onChange={handleTabChange} sx={{ mb: 2 }}>
            <Tab label="Issues" />
            <Tab label="Confluence" />
            <Tab label="Stack Overflow" />
          </Tabs>

          {/* Issues Tab */}
          {tab === 0 && (
            <Box>
              <Typography variant="h5" gutterBottom>
                Issue Results ({combinedResults.filter((result) => result.type === 'jira' || result.type === 'msg' || result.type === 'vector_issue').length})
              </Typography>
              <Grid container spacing={3}>
                {combinedResults.filter((result) => result.type === 'jira' || result.type === 'msg' || result.type === 'vector_issue').map((issue) => (
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
                        <Button size="small" variant="outlined" onClick={() => handleViewIssue(issue.id)}>
                          View Details
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Confluence Tab */}
          {tab === 1 && (
            <Box>
              <Typography variant="h5" gutterBottom>
                Confluence Results ({combinedResults.filter((result) => result.type === 'confluence').length})
              </Typography>
              <Grid container spacing={3}>
                {combinedResults.filter((result) => result.type === 'confluence').map((page) => (
                  <Grid item xs={12} key={page.id}>
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
                        </Box>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" sx={{ mb: 2 }}>
                          {page.description?.length > 200
                            ? `${page.description.substring(0, 200)}...`
                            : page.description}
                        </Typography>
                      </CardContent>
                      <CardActions>
                        {getResultUrl(page) && (
                          <Button
                            size="small"
                            variant="text"
                            color="primary"
                            href={getResultUrl(page)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View Page
                          </Button>
                        )}
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
          {/* Stack Overflow Tab */}
          {tab === 2 && (
            <Box>
              <Typography variant="h5" gutterBottom>
                Stack Overflow Results ({combinedResults.filter((result) => result.type === 'stackoverflow').length})
              </Typography>
              <Grid container spacing={3}>
                {combinedResults.filter((result) => result.type === 'stackoverflow').map((item, idx) => (
                  <Grid item xs={12} key={item.id || idx}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {item.title}
                        </Typography>
                        <Box sx={{ display: 'flex', mb: 1 }}>
                          {item.similarity_score !== undefined && (
                            <Chip
                              label={`Similarity: ${(item.similarity_score * 100).toFixed(2)}%`}
                              color="secondary"
                              size="small"
                              sx={{ mr: 1 }}
                            />
                          )}
                          <Chip
                            label={item.soType === 'question' ? 'Question' : 'Answer'}
                            color={item.soType === 'question' ? 'primary' : 'info'}
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        </Box>
                        <Divider sx={{ my: 1 }} />
                        <Typography variant="body2" sx={{ mb: 2 }}>
                          {item.description?.length > 200
                            ? `${item.description.substring(0, 200)}...`
                            : item.description}
                        </Typography>
                      </CardContent>
                      <CardActions>
                        {getResultUrl(item) && (
                          <Button
                            size="small"
                            variant="text"
                            color="primary"
                            href={getResultUrl(item)}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            View on Stack Overflow
                          </Button>
                        )}
                      </CardActions>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </>
      )}
    </Box>
  );
};

export default SearchPage;