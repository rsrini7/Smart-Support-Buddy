import React from 'react';
import { Typography, Box, Paper, Grid, Button, Card, CardContent, CardActions } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const HomePage = () => {
  return (
    <Box>
      <Paper sx={{ p: 4, mb: 4, backgroundColor: 'primary.light', color: 'white' }}>
        <Typography variant="h4" gutterBottom>
          Support Buddy
        </Typography>
        <Typography variant="subtitle1">
          Easily manage, search, and analyze support issues / queries using MSG files and Jira integration
        </Typography>
        <Box sx={{ mt: 3 }}>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/ingest-msg-files"
            sx={{ mr: 2 }}
          >
            Ingest MSG
          </Button>
          <Button
            variant="contained"
            color="secondary"
            component={RouterLink}
            to="/upload"
            sx={{ mr: 2 }}
          >
            Upload Issue
          </Button>
          <Button 
            variant="outlined" 
            color="inherit" 
            component={RouterLink} 
            to="/search"
          >
            Search Issues
          </Button>
        </Box>
      </Paper>

      <Typography variant="h5" gutterBottom>
        Features
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                MSG File Parsing
              </Typography>
              <Typography variant="body2">
                Upload and parse Microsoft Outlook MSG files containing production issue details
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={RouterLink} to="/upload">
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Jira Integration
              </Typography>
              <Typography variant="body2">
                Link issues with Jira tickets to correlate information and track resolution
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={RouterLink} to="/upload?tab=jira">
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Semantic Search
              </Typography>
              <Typography variant="body2">
                Find similar issues using vector search to quickly identify solutions
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={RouterLink} to="/search">
                Try It
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HomePage;