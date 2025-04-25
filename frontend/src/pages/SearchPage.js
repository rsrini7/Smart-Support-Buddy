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
  Tab,
  Checkbox, // Import Checkbox
  FormControlLabel // Import FormControlLabel
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
  const [singlePageResult, setSinglePageResult] = useState(true);
  const [useLLM, setUseLLM] = useState(false); // State for LLM checkbox
  const [llmSummary, setLlmSummary] = useState(''); // State for LLM Action

  useEffect(() => {
    // Perform search if we have initial search parameters
    if (location.state?.searchQuery) {
      // Check if LLM was used in the previous state if needed
      // setUseLLM(location.state?.useLLM || false);
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
    setLlmSummary(''); // Clear previous summary

    try {
      const response = await fetch(`${BACKEND_API_BASE}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_text: queryText,
          limit: 10,
          use_llm: useLLM // Send LLM flag to backend
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Search failed');
      }

      setCombinedResults(data.results || []);
      setLlmSummary(data.llm_summary || ''); // Set LLM Action if available
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
        searchQuery: queryText,
        // Persist LLM state if needed
        // useLLM: useLLM
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

          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSearch}
              disabled={loading || !queryText}
            >
              {loading ? <CircularProgress size={24} /> : 'Search'}
            </Button>
            {/* Keep Single Page Result Checkbox */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={singlePageResult}
                  onChange={(e) => setSinglePageResult(e.target.checked)}
                  id="singlePageResult"
                />
              }
              label="Single Page Result"
            />
            {/* Add LLM Checkbox */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={useLLM}
                  onChange={(e) => setUseLLM(e.target.checked)}
                  id="useLLM"
                />
              }
              label="LLM Action"
            />
          </Box>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Display LLM Action if available */}
      {llmSummary && (
        <Paper
          sx={(theme) => ({
            p: 2,
            mb: 3,
            background: theme.palette.mode === 'dark'
              ? 'linear-gradient(135deg, #23272a 0%, #181a1b 100%)'
              : theme.palette.info.light,
            color: theme.palette.mode === 'dark'
              ? theme.palette.text.primary
              : theme.palette.text.primary,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: 3,
            borderRadius: 2,
            transition: 'background 0.3s, color 0.3s',
          })}
        >
          <Typography
            variant="h6"
            gutterBottom
            sx={(theme) => ({
              color: theme.palette.mode === 'dark'
                ? theme.palette.info.light
                : theme.palette.info.dark,
              fontWeight: 700,
              letterSpacing: 1,
              mb: 1
            })}
          >
            LLM Action
          </Typography>
          <Typography
            variant="body1"
            sx={(theme) => ({
              whiteSpace: 'pre-wrap',
              fontFamily: 'inherit',
              color: theme.palette.text.primary,
              fontSize: 16,
              lineHeight: 1.6,
            })}
          >
            {llmSummary}
          </Typography>
        </Paper>
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
            All Results ({combinedResults.length})
          </Typography>
          <Grid container spacing={3}>
            {combinedResults.length > 0 ? (
              combinedResults.map((result, idx) => (
                <Grid item xs={12} key={result.id || idx}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {result.type === 'confluence' && result.metadata && result.metadata.display_title
                          ? result.metadata.display_title
                          : result.type === 'confluence' && result.metadata && result.metadata.section_text
                            ? result.metadata.section_text.split('\n')[0].slice(0, 120)
                            : result.title || result.summary || result.url}
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
                        {/* Confluence section anchor if present */}
                        {result.type === 'confluence' && result.metadata && result.metadata.section_anchor && (
                          <Chip
                            label={`Section: ${result.metadata.section_anchor}`}
                            color="info"
                            size="small"
                            sx={{ mr: 1 }}
                            component="a"
                            href={`${getResultUrl(result)}#${result.metadata.section_anchor}`}
                            target="_blank"
                            clickable
                          />
                        )}
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
                        {result.type === 'confluence' && result.metadata && result.metadata.section_text
                          ? (result.metadata.section_text.length > 200
                              ? `${result.metadata.section_text.substring(0, 200)}...`
                              : result.metadata.section_text)
                          : result.type === 'confluence' && result.metadata && result.metadata.content
                            ? (result.metadata.content.length > 200
                                ? `${result.metadata.content.substring(0, 200)}...`
                                : result.metadata.content)
                            : (result.description?.length > 200
                                ? `${result.description.substring(0, 200)}...`
                                : result.description)}
                      </Typography>
                      {/* Confluence: show section context if available */}
                      {result.type === 'confluence' && result.metadata && result.metadata.section_text && (
                        <Box sx={{ mb: 1 }}>
                          <Typography variant="subtitle2">Matched Section:</Typography>
                          <Typography variant="body2">
                            {result.metadata.section_text.length > 200
                              ? `${result.metadata.section_text.substring(0, 200)}...`
                              : result.metadata.section_text}
                          </Typography>
                        </Box>
                      )}
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
              <Typography variant="h5" gutterBottom sx={{
                color: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.text.primary
                  : 'inherit',
                background: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.background.paper
                  : 'transparent',
                p: 1,
                borderRadius: 1,
                mb: 1
              }}>
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
              <Typography variant="h5" gutterBottom sx={{
                color: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.text.primary
                  : 'inherit',
                background: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.background.paper
                  : 'transparent',
                p: 1,
                borderRadius: 1,
                mb: 1
              }}>
                Confluence Results ({combinedResults.filter((result) => result.type === 'confluence').length})
              </Typography>
              <Grid container spacing={3}>
                {combinedResults.filter((result) => result.type === 'confluence').map((page) => (
                  <Grid item xs={12} key={page.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {page.metadata && page.metadata.display_title
                            ? page.metadata.display_title
                            : page.metadata && page.metadata.section_text
                              ? page.metadata.section_text.split('\n')[0].slice(0, 120)
                              : page.title}
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
                          {page.metadata && page.metadata.section_text
                            ? (page.metadata.section_text.length > 200
                                ? `${page.metadata.section_text.substring(0, 200)}...`
                                : page.metadata.section_text)
                            : page.metadata && page.metadata.content
                              ? (page.metadata.content.length > 200
                                  ? `${page.metadata.content.substring(0, 200)}...`
                                  : page.metadata.content)
                              : (page.description?.length > 200
                                  ? `${page.description.substring(0, 200)}...`
                                  : page.description)}
                        </Typography>
                        {/* Confluence: show section context if available */}
                        {page.metadata && page.metadata.section_text && (
                          <Box sx={{ mb: 1 }}>
                            <Typography variant="subtitle2">Matched Section:</Typography>
                            <Typography variant="body2">
                              {page.metadata.section_text.length > 200
                                ? `${page.metadata.section_text.substring(0, 200)}...`
                                : page.metadata.section_text}
                            </Typography>
                          </Box>
                        )}
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
              <Typography variant="h5" gutterBottom sx={{
                color: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.text.primary
                  : 'inherit',
                background: (theme) => theme.palette.mode === 'dark'
                  ? theme.palette.background.paper
                  : 'transparent',
                p: 1,
                borderRadius: 1,
                mb: 1
              }}>
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