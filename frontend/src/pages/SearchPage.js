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

const SearchPage = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Initialize state from location if available
  const [queryText, setQueryText] = useState(() => location.state?.searchQuery || '');
  const [jiraTicketId, setJiraTicketId] = useState(() => location.state?.searchJiraId || '');
  const [issueResults, setIssueResults] = useState(() => location.state?.searchResults || []);
  const [confluenceResults, setConfluenceResults] = useState([]);
  const [stackOverflowResults, setStackOverflowResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tab, setTab] = useState(0);
  const [singlePageResult, setSinglePageResult] = useState(false);

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
      // Do NOT clear results if search is invalid
      return;
    }
    // Only clear results if a valid search is being performed

    setLoading(true);
    setError('');
    setIssueResults([]);
    setConfluenceResults([]);
    setStackOverflowResults([]);

    // Search issues
    let issueError = '';

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

      // New backend returns { vector_issues, confluence_results, stackoverflow_results }
      setIssueResults(data.vector_issues || []);
      setConfluenceResults(
        Array.isArray(data.confluence_results)
          ? data.confluence_results
          : data.confluence_results?.results || []
      );
      setStackOverflowResults(
        Array.isArray(data.stackoverflow_results)
          ? data.stackoverflow_results
          : data.stackoverflow_results?.results || []
      );
    } catch (err) {
      issueError = err.message;
      setError(issueError);
    } finally {
      setLoading(false);
    }

    // The separate fetches for confluence and stackoverflow have been removed. All results now come from the main /api/search call.
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
      <Typography variant="h4" gutterBottom color="text.primary">
        Search Support Issues / Queries
      </Typography>

      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="body1" gutterBottom>
          Search for support issues / queries by description or Jira ticket ID.
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

          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={loading || (!queryText && !jiraTicketId)}
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
        // Unified single result tab
        <Box>
          <Typography variant="h5" gutterBottom>
            All Results
          </Typography>
          <Grid container spacing={3}>
            {[
              ...issueResults.map((issue) => ({
                type: issue.jira_ticket_id ? 'jira' : 'msg',
                id: issue.id,
                title: issue.title || issue.summary,
                description: issue.description,
                similarity_score: issue.similarity_score,
                received_date: issue.received_date || issue.created_at,
                root_cause: issue.root_cause,
                jira_ticket_id: issue.jira_ticket_id,
                onView: () => handleViewIssue(issue.id),
              })),
              ...confluenceResults.map((page) => ({
                type: 'confluence',
                id: page.page_id,
                title: page.title,
                description: page.content,
                similarity_score: page.similarity_score,
                url: page.metadata?.confluence_url,
              })),
              ...stackOverflowResults.map((item, idx) => ({
                type: 'stackoverflow',
                id: item.item_id || idx,
                title: item.title,
                description: item.content,
                similarity_score: item.similarity_score,
                url: item.metadata?.url,
                soType: item.metadata?.type,
              })),
            ].length > 0 ? (
              [
                ...issueResults.map((issue) => ({
                  type: issue.jira_ticket_id ? 'jira' : 'msg',
                  id: issue.id,
                  title: issue.title || issue.summary,
                  description: issue.description,
                  similarity_score: issue.similarity_score,
                  received_date: issue.received_date || issue.created_at,
                  root_cause: issue.root_cause,
                  jira_ticket_id: issue.jira_ticket_id,
                  onView: () => handleViewIssue(issue.id),
                })),
                ...confluenceResults.map((page) => ({
                  type: 'confluence',
                  id: page.page_id,
                  title: page.title,
                  description: page.content,
                  similarity_score: page.similarity_score,
                  url: page.metadata?.confluence_url,
                })),
                ...stackOverflowResults.map((item, idx) => ({
                  type: 'stackoverflow',
                  id: item.item_id || idx,
                  title: item.title,
                  description: item.content,
                  similarity_score: item.similarity_score,
                  url: item.metadata?.url,
                  soType: item.metadata?.type,
                })),
              ].map((result, idx) => (
                <Grid item xs={12} key={result.id || idx}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {result.title}
                      </Typography>
                      <Box sx={{ display: 'flex', mb: 1, alignItems: 'center' }}>
                        {/* Source tag */}
                        <Chip
                          label={
                            result.type === 'jira'
                              ? 'Jira'
                              : result.type === 'msg'
                              ? 'Msg'
                              : result.type === 'confluence'
                              ? 'Confluence'
                              : result.type === 'stackoverflow'
                              ? 'Stack Overflow'
                              : 'Other'
                          }
                          color={
                            result.type === 'jira'
                              ? 'primary'
                              : result.type === 'msg'
                              ? 'info'
                              : result.type === 'confluence'
                              ? 'success'
                              : result.type === 'stackoverflow'
                              ? 'warning'
                              : 'default'
                          }
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        {/* Extra tags */}
                        {result.jira_ticket_id && (
                          <Chip
                            label={result.jira_ticket_id}
                            color="primary"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        {result.similarity_score !== undefined && (
                          <Chip
                            label={`Similarity: ${(result.similarity_score * 100).toFixed(2)}%`}
                            color="secondary"
                            size="small"
                            sx={{ mr: 1 }}
                          />
                        )}
                        {result.received_date && (
                          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                            Received: {formatDate(result.received_date)}
                          </Typography>
                        )}
                        {result.type === 'confluence' && result.url && (
                          <Typography variant="body2" color="text.secondary">
                            <Link href={result.url} target="_blank" rel="noopener noreferrer" color="primary" underline="hover">
                              View Page
                            </Link>
                          </Typography>
                        )}
                        {result.type === 'stackoverflow' && result.url && (
                          <Typography variant="body2" color="text.secondary">
                            <Link href={result.url} target="_blank" rel="noopener noreferrer" color="primary" underline="hover">
                              View on Stack Overflow
                            </Link>
                          </Typography>
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
                    {result.onView && (
                      <CardActions>
                        <Button size="small" onClick={result.onView}>
                          View Details
                        </Button>
                      </CardActions>
                    )}
                  </Card>
                </Grid>
              ))
            ) : loading ? null : (
              <Grid item xs={12}>
                <Paper sx={{ p: 3, textAlign: 'center' }}>
                  <Typography variant="body1">
                    {queryText || jiraTicketId
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
                                <Link href={page.metadata.confluence_url} target="_blank" rel="noopener noreferrer" color="primary" underline="hover">
                                  View Page
                                </Link>
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
          {/* Stack Overflow Tab */}
          {tab === 2 && (
            stackOverflowResults.length > 0 ? (
              <Box>
                <Typography variant="h5" gutterBottom>
                  Stack Overflow Results ({stackOverflowResults.length})
                </Typography>
                <Grid container spacing={3}>
                  {stackOverflowResults.map((item, idx) => (
                    <Grid item xs={12} key={item.item_id || idx}>
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
                            <Typography variant="body2" color="text.secondary">
                              {item.metadata?.url && (
                                <Link href={item.metadata.url} target="_blank" rel="noopener noreferrer" color="primary" underline="hover">
                                  View on Stack Overflow
                                </Link>
                              )}
                            </Typography>
                            <Chip
                              label={item.metadata?.type === 'question' ? 'Question' : 'Answer'}
                              color={item.metadata?.type === 'question' ? 'primary' : 'info'}
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="body2" sx={{ mb: 2 }}>
                            {item.content?.length > 200
                              ? `${item.content.substring(0, 200)}...`
                              : item.content}
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
                  {queryText ? 'No Stack Overflow results found. Try a different search query.' : 'Enter a search query to begin.'}
                </Typography>
              </Paper>
            )
          )}
        </>
      )}
    </Box>
  );
};

export default SearchPage;