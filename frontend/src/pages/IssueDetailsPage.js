import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { BACKEND_API_BASE } from '../settings';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Link,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';

const IssueDetailsPage = () => {
  const { issueId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const previousQuery = location.state?.searchQuery || '';
  const previousJiraId = location.state?.searchJiraId || '';
  const [issue, setIssue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const handleGoBack = () => {
    // Check if we have search state to return to
    const searchState = location.state;
    if (searchState?.searchResults) {
      navigate('/search', { state: searchState });
    } else {
      navigate(-1);
    }
  };

  useEffect(() => {
    const fetchIssueDetails = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${BACKEND_API_BASE}/issues/${issueId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch issue details');
        }

        const data = await response.json();
        setIssue(data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load issue details');
        setLoading(false);
      }
    };

    fetchIssueDetails();
  }, [issueId]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
  };

  const handleDeleteConfirm = async () => {
    setDeleteLoading(true);
    try {
      const response = await fetch(`${BACKEND_API_BASE}/issues/${issueId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete issue');
      }

      // Navigate back to search page after successful deletion
      navigate('/search', { state: { searchQuery: previousQuery, searchJiraId: previousJiraId } });
    } catch (err) {
      setError(err.message);
      setDeleteDialogOpen(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!issue) {
    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        Issue not found
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 2 }}>
        <Button variant="outlined" onClick={handleGoBack} sx={{ mr: 2 }}>
          Back
        </Button>
      </Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Issue Details
        </Typography>
        <Button
          variant="contained"
          color="error"
          onClick={handleDeleteClick}
          disabled={loading || deleteLoading}
        >
          Delete Issue
        </Button>
      </Box>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          {issue.title}
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
          {issue.jira_ticket_id && (
            <Chip 
              label={`Jira: ${issue.jira_ticket_id}`} 
              color="primary" 
              size="small" 
            />
          )}
          {issue.jira_data?.status && (
            <Chip 
              label={`Status: ${issue.jira_data.status}`} 
              color={issue.jira_data.status === 'Resolved' ? 'success' : 'warning'} 
              size="small" 
            />
          )}
          {issue.jira_data?.priority && (
            <Chip 
              label={`Priority: ${issue.jira_data.priority}`} 
              color={issue.jira_data.priority === 'High' ? 'error' : 'default'} 
              size="small" 
            />
          )}
          <Chip 
            label={`Received: ${formatDate(issue.received_date)}`} 
            variant="outlined" 
            size="small" 
          />
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Overview" />
          <Tab label="MSG Details" />
          <Tab label="Jira Details" />
        </Tabs>
        
        {tabValue === 0 && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                      {issue.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              

            </Grid>
          </Box>
        )}
        
        {tabValue === 1 && issue.msg_data && (
          <Box>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Subject: {issue.msg_data.subject}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  From: {issue.msg_data.sender}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  To: {Array.isArray(issue.msg_data.recipients) ? issue.msg_data.recipients.join(', ') : issue.msg_data.recipients}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Received: {formatDate(issue.msg_data.received_date)}
                </Typography>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {issue.msg_data.body}
                </Typography>
                
                {issue.msg_data.attachments && issue.msg_data.attachments.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Attachments:
                    </Typography>
                    <List dense>
                      {issue.msg_data.attachments.map((attachment, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={attachment} />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        )}
        
        {tabValue === 2 && issue.jira_data && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Ticket Information
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText primary="Key" secondary={issue.jira_data.key} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Summary" secondary={issue.jira_data.summary} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Status" secondary={issue.jira_data.status} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Priority" secondary={issue.jira_data.priority} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Created" secondary={formatDate(issue.jira_data.created)} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Updated" secondary={formatDate(issue.jira_data.updated)} />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      People
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText primary="Assignee" secondary={issue.jira_data.assignee || 'Unassigned'} />
                      </ListItem>
                      <ListItem>
                        <ListItemText primary="Reporter" secondary={issue.jira_data.reporter || 'Unknown'} />
                      </ListItem>
                    </List>
                    
                    <Typography variant="h6" sx={{ mt: 2 }} gutterBottom>
                      Classification
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Components" 
                          secondary={issue.jira_data.components?.join(', ') || 'None'} 
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Labels" 
                          secondary={
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {issue.jira_data.labels?.map((label, index) => (
                                <Chip key={index} label={label} size="small" />
                              )) || 'None'}
                            </Box>
                          } 
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      View in Jira
                    </Typography>
                    <Link 
                      href={`${process.env.REACT_APP_JIRA_BASE_URL}/browse/${issue.jira_data.key}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                    >
                      Open ticket {issue.jira_data.key} in Jira
                    </Link>
                  </CardContent>
                </Card>
              </Grid>

              {issue.jira_data?.comments && issue.jira_data.comments.length > 0 && (
                <Grid item xs={12}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Jira Comments
                      </Typography>
                      <List dense>
                        {issue.jira_data.comments.map((comment, index) => (
                          <ListItem key={index} alignItems="flex-start">
                            <ListItemText
                              primary={
                                typeof comment.author === 'string'
                                  ? comment.author
                                  : (comment.author?.displayName || 'Unknown Author')
                              }
                              secondary={comment.body || ''}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          </Box>
        )}
      </Paper>
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Delete Issue</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this issue? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={deleteLoading}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" disabled={deleteLoading} autoFocus>
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IssueDetailsPage;